"""Unit tests for fetch_sector_performance() in index_data.py.

These tests verify that the sector-performance widget correctly skips
holiday placeholder rows (is_holiday=True / close=None) when picking the
comparison dates, so it doesn't fall back to stale test data when the most
recent date in the DB is a holiday.
"""
import datetime as dt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Asset, DailyPrice


@pytest.fixture
def fresh_db():
    """In-memory DB with a known mix of real trading days + a holiday."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Two equity assets in different sectors
    a1 = Asset(symbol='RELIANCE.NS', name='Reliance', exchange='NSE',
               sector='Energy', type='equity')
    a2 = Asset(symbol='TCS.NS', name='TCS', exchange='NSE',
               sector='IT', type='equity')
    session.add_all([a1, a2])
    session.commit()

    # 2026-09-06 (prev trading day) — real data
    session.add_all([
        DailyPrice(asset_id=a1.id, date=dt.date(2026, 9, 6),
                   open=100, high=105, low=99, close=100.0,
                   adj_close=100.0, volume=1000, is_holiday=False),
        DailyPrice(asset_id=a2.id, date=dt.date(2026, 9, 6),
                   open=200, high=205, low=199, close=200.0,
                   adj_close=200.0, volume=2000, is_holiday=False),
    ])
    # 2026-09-07 (latest trading day) — real data
    session.add_all([
        DailyPrice(asset_id=a1.id, date=dt.date(2026, 9, 7),
                   open=105, high=108, low=98, close=104.0,
                   adj_close=104.0, volume=1500, is_holiday=False),
        DailyPrice(asset_id=a2.id, date=dt.date(2026, 9, 7),
                   open=205, high=210, low=200, close=205.0,
                   adj_close=205.0, volume=2500, is_holiday=False),
    ])
    # 2026-09-08 (latest date in DB) — holiday placeholder, close=None
    session.add_all([
        DailyPrice(asset_id=a1.id, date=dt.date(2026, 9, 8),
                   open=None, high=None, low=None, close=None,
                   adj_close=None, volume=0, is_holiday=True),
        DailyPrice(asset_id=a2.id, date=dt.date(2026, 9, 8),
                   open=None, high=None, low=None, close=None,
                   adj_close=None, volume=0, is_holiday=True),
    ])
    session.commit()

    yield session
    session.close()


def test_sector_performance_skips_holiday_latest_date(fresh_db, monkeypatch):
    """When the most recent DB date is a holiday placeholder, the function
    must still return real sector data from the previous trading day.

    Regression test: previously the function picked 2026-09-08 as latest,
    found close=None for every stock, returned [], and the dashboard fell
    back to the 6-sector TEST_SECTOR_DATA.
    """
    import index_data
    # fetch_sector_performance() does `from models import get_session`,
    # so patch it on the models module.
    import models
    monkeypatch.setattr(models, 'get_session', lambda: fresh_db)
    # Ensure no cached result from a prior call.
    index_data._cache.pop('sector_performance', None)

    sectors = index_data.fetch_sector_performance()

    assert len(sectors) == 2, f'Expected 2 sectors, got {sectors}'
    names = {s['name'] for s in sectors}
    assert names == {'Energy', 'IT'}

    # Verify the percentages are computed against the last two real trading
    # days (09-07 vs 09-06), NOT against the holiday 09-08.
    # RELIANCE: 104 vs 100 -> +4.0%  (Energy)
    # TCS:      205 vs 200 -> +2.5%  (IT)
    by_name = {s['name']: s for s in sectors}
    assert abs(by_name['Energy']['pct'] - 4.0) < 1e-6
    assert abs(by_name['IT']['pct'] - 2.5) < 1e-6
    assert by_name['Energy']['stocks_count'] == 1
    assert by_name['IT']['stocks_count'] == 1


def test_sector_performance_empty_when_no_real_trading_days(monkeypatch):
    """When the DB has only holiday rows, return [] (no fallback)."""
    import index_data
    import models
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    a = Asset(symbol='X.NS', name='X', exchange='NSE',
              sector='Energy', type='equity')
    session.add(a)
    session.commit()
    session.add(DailyPrice(asset_id=a.id, date=dt.date(2026, 9, 8),
                           open=None, high=None, low=None, close=None,
                           adj_close=None, volume=0, is_holiday=True))
    session.commit()

    monkeypatch.setattr(models, 'get_session', lambda: session)
    index_data._cache.pop('sector_performance', None)

    sectors = index_data.fetch_sector_performance()
    assert sectors == []
    session.close()


def test_sector_performance_skips_interleaved_holiday(monkeypatch):
    """A holiday sandwiched between two real trading days must be skipped."""
    import index_data
    import models
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    a = Asset(symbol='Y.NS', name='Y', exchange='NSE',
              sector='Banking', type='equity')
    session.add(a)
    session.commit()
    # 09-06 real, 09-07 holiday, 09-08 real
    session.add_all([
        DailyPrice(asset_id=a.id, date=dt.date(2026, 9, 6),
                   open=100, high=105, low=99, close=100.0,
                   adj_close=100.0, volume=100, is_holiday=False),
        DailyPrice(asset_id=a.id, date=dt.date(2026, 9, 7),
                   open=None, high=None, low=None, close=None,
                   adj_close=None, volume=0, is_holiday=True),
        DailyPrice(asset_id=a.id, date=dt.date(2026, 9, 8),
                   open=105, high=110, low=104, close=108.0,
                   adj_close=108.0, volume=150, is_holiday=False),
    ])
    session.commit()

    monkeypatch.setattr(models, 'get_session', lambda: session)
    index_data._cache.pop('sector_performance', None)

    sectors = index_data.fetch_sector_performance()
    assert len(sectors) == 1
    assert sectors[0]['name'] == 'Banking'
    # latest=09-08 (108), prev=09-06 (100) -> +8.0%
    assert abs(sectors[0]['pct'] - 8.0) < 1e-6
    session.close()
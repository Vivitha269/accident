# API Response Speedup TODO

## Issues
- Overpass API calls slow (30s timeout).
- Sequential police + hospitals.
- No cache/retry.

## Plan Steps
- [ ] Step 1: Add httpx to requirements.txt + pip install
- [ ] Step 2: services/places.py async httpx, lru_cache, gather police/hospitals
- [ ] Step 3: main.py await async services
- [ ] Step 4: Reduce timeout 10s, add fallbacks
- [ ] Step 5: Test /accident response <5s

Next: Install httpx.

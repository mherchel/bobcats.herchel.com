# PWA Implementation Plan - Lacrosse Goal Songs Soundboard

## Overview

Convert the existing web-based soundboard into a Progressive Web App (PWA) that works completely offline on mobile devices during lacrosse games.

**Primary Use Case**: Coaches/operators need instant, reliable access to all goal songs during games where internet connectivity is unreliable or unavailable.

**Current State**: Vanilla JS web app that preloads all audio files on page load (~45MB). Works online, fails completely when offline.

---

## Goals & Success Criteria

### Must Have
- ✓ Install to iOS home screen (Safari)
- ✓ Function 100% offline (all 36 songs play instantly)
- ✓ Updates propagate when new songs are added
- ✓ Total cache size stays under typical mobile storage limits

### Success Metrics
- App installs on iOS without errors
- All songs play in airplane mode with zero network requests
- Updates deploy without requiring user to uninstall/reinstall
- No regression in existing functionality (preload button, stop button, navigation)

### Nice to Have
- Install on Android
- Update notifications
- Storage usage monitoring
- Offline/online status indicators

---

## Core Architectural Decisions

### Decision 1: Path Strategy

**Problem**: App may be deployed to root domain, subdomain, or subdirectory.

**Options**:
- A) Absolute paths (`/manifest.json`) - simple, breaks in subdirectories
- B) Relative paths (`./manifest.json`) - works anywhere, harder to reason about
- C) Configurable base path - flexible, requires build step/configuration

**Decision**: **Option B - Relative paths throughout**

**Why**: No build step required, works in any deployment location, aligns with existing "no build process" philosophy.

**Impact**: All paths in manifest.json, service worker, and HTML must use `./` prefix. Requires careful testing to ensure consistency.

---

### Decision 2: Cache Strategy

**Problem**: Need different caching strategies for different asset types.

**Options**:
- A) Cache-first for everything - fast, but stale data
- B) Network-first for everything - always fresh, but slow/fails offline
- C) Hybrid: cache-first for static, network-first for data

**Decision**: **Modified Option C - Cache-first for everything, background update check**

**Why**:
- Primary use case is offline during games - can't wait for network
- JSON files (~10KB) are tiny compared to audio (~45MB)
- Background update check solves staleness without blocking

**Strategy**:
1. **Static assets** (HTML/CSS/JS/icons): Cache-first, never expire during session
2. **Audio files**: Cache-first, never expire during session
3. **JSON files**: Cache-first, but check network in parallel and notify if newer version available
4. **Update flow**: Don't auto-apply updates - let user choose when to refresh

**Tradeoff**: User might not see newly added songs immediately, but they'll never experience a loading delay.

---

### Decision 3: Interaction with Existing Preload Logic

**Problem**: App currently preloads all audio files using `<audio>` elements. Service worker will cache the same files. This could result in ~90MB download on first visit.

**Current app.js behavior**:
```
On page load → preload all audio files for current team → instant playback
```

**Options**:
- A) Keep both preload and SW cache - wasteful but safe
- B) Remove app preload, rely on SW cache - cleaner, but need to verify audio plays from cache
- C) Modify app to skip preload if SW cache exists - optimal but adds complexity

**Decision**: **Option B - Remove existing preload logic, rely on service worker cache**

**Why**:
- Service worker cache serves same purpose (instant playback)
- Eliminates duplicate downloads
- Simpler mental model
- Modern Audio API works seamlessly with cached responses

**Implementation requirement**: Verify that Audio elements can play directly from SW cache (they can in all modern browsers).

**Risk**: If SW install fails, audio won't preload. Mitigation: Graceful degradation in app.js (detect SW status, fall back to original preload if needed).

---

### Decision 4: Entry Point Strategy

**Problem**: Three HTML pages (index, varsity, jv) but PWA needs a single `start_url`.

**Context**: Coaches might bookmark/want direct access to their team's page.

**Options**:
- A) Single PWA, always start at index.html - simple, consistent
- B) Two PWAs (one for varsity, one for JV) - direct access, but maintenance overhead
- C) Single PWA, but remember last visited page - complex state management

**Decision**: **Option A - Single PWA starting at index.html**

**Why**:
- Both teams at same school, likely same person managing
- Landing page provides context and choice
- Simpler maintenance (one manifest, one SW)
- Can still bookmark specific team pages for direct access in browser

**Tradeoff**: JV coach can't install "JV Goal Songs" as separate app, but can bookmark varsity.html directly.

---

### Decision 5: Cache Versioning Strategy

**Problem**: How to trigger cache updates when new songs are added?

**Options**:
- A) Manual version bump (`const VERSION = 'v2'`) - simple, error-prone
- B) Timestamp-based (`const VERSION = '2026-02-15-001'`) - slightly better, still manual
- C) Hash-based (generated from sounds.json) - automatic, requires build step
- D) Generate SW file with embedded file list + hash - most reliable, complex

**Decision**: **Option C - Hash-based versioning with helper script**

**Why**:
- Cannot forget to update version (it's automated)
- Clear signal when content changes
- No build step for main app, just run Python script when updating songs

**Implementation**:
- Extend `process_songs.py` to generate `sw.js` with computed hash
- Hash based on contents of sounds.json files
- Service worker includes: `const CACHE_VERSION = 'lacrosse-goals-${HASH}'`

**Benefit**: `process_songs.py` → generates JSON + generates SW with new hash → deploy → users auto-detect update.

---

### Decision 6: Graceful Degradation Strategy

**Problem**: If some audio files fail to cache, should the app fail completely or partially?

**Options**:
- A) All-or-nothing: If any file fails, SW install fails - strict, safe
- B) Critical assets required, audio optional - pragmatic, complex
- C) Best-effort: cache what you can, warn about failures - most flexible

**Decision**: **Option B - Critical assets required, audio files optional**

**Why**:
- One corrupted audio file shouldn't brick entire app
- Better to have 35/36 songs than 0/36 songs
- Can log failures for debugging

**Strategy**:
1. Critical assets (HTML/CSS/JS/JSON) must cache successfully - install fails if these fail
2. Audio files cached individually - log failures but continue
3. At end of install, log summary: "32/36 audio files cached"
4. App functions with partial audio cache

**Edge case**: What if user clicks button for missing audio? Graceful error: "Song unavailable offline" toast.

---

## Key Technical Challenges

### Challenge 1: Storage Limits

**Issue**: iOS doesn't have a fixed storage limit. Dynamic quota based on device storage. Can be evicted under memory pressure.

**Solution**:
- Check quota before caching using `navigator.storage.estimate()`
- Request persistent storage with `navigator.storage.persist()` to prevent eviction
- Monitor usage and warn if approaching 80% of quota
- Current size (~45MB) is safe for most devices, but plan for growth

**Growth planning**: At ~1.2MB per song, can add ~15-20 more songs before approaching typical limits. Beyond that, need to:
- Reduce bitrate (128kbps → 96kbps)
- Split into separate varsity/JV PWAs
- Implement selective caching

---

### Challenge 2: Update Detection Without Breaking Active Sessions

**Issue**: User might be playing songs when update is available. Forceful update would interrupt playback.

**Solution**:
- New service worker installs in background (doesn't activate)
- Show non-intrusive update banner: "New songs available"
- User chooses when to update (button in banner)
- Only on user action: activate new SW and reload page
- If user dismisses banner, update applies automatically on next app open

**UX**: Update during halftime, not during goal celebration.

---

### Challenge 3: Testing Offline Functionality

**Issue**: Hard to verify everything works offline without real-world testing.

**Testing strategy**:
1. **DevTools offline mode**: Verify cache contents and fetch interception
2. **Real device airplane mode**: Ensure no network requests leak through
3. **Staged testing**: Test with subset of songs first, then full set
4. **Cache inspection**: Verify all audio files actually cached (count them)

**Acceptance criteria**:
- Open DevTools Network tab → Enable offline → Refresh → All resources from SW cache
- Open iOS app in airplane mode → All songs play without delay
- Check cache size: Should be ~45-46MB (not 90MB from double-download)

---

## Implementation Phases

### Phase 1: PWA Manifest & Icons
**Goal**: Make app installable on iOS/Android

**Deliverables**:
- manifest.json with app metadata, relative paths, icon references
- Icon set (10 sizes from 72px to 512px)
- Separate maskable icons for Android (with safe area padding)
- HTML `<head>` tags for manifest + iOS-specific meta tags

**Exit criteria**:
- iOS Safari shows "Add to Home Screen" option
- App icon appears on home screen
- App opens in standalone mode (no browser UI)

---

### Phase 2: Service Worker - Cache Everything
**Goal**: Enable complete offline functionality

**Deliverables**:
- sw.js with install/activate/fetch handlers
- Cache strategy: cache-first for all assets
- Graceful degradation for audio files
- Registration code in app.js (not inline in HTML)

**Exit criteria**:
- DevTools shows SW active and cache populated (~45MB)
- App works in airplane mode (all songs play)
- No existing preload logic executed (verify in network tab)

---

### Phase 3: Update Mechanism
**Goal**: Seamless updates when songs are added

**Deliverables**:
- Modified process_songs.py to generate sw.js with hash-based version
- Update detection logic in app.js
- Update notification UI (banner at bottom of screen)
- Manual update trigger (button in banner)

**Exit criteria**:
- Add test song → run process_songs.py → deploy
- Open app → See "New songs available" banner
- Click update → Page reloads with new song

---

### Phase 4: Refinements & Polish
**Goal**: Nice-to-have features

**Deliverables** (optional):
- Online/offline status indicator
- Storage quota monitoring
- Persistent storage request
- Splash screens for iOS

**Exit criteria**: Based on time/priority

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Service worker fails to install | App doesn't work offline | Medium | Graceful degradation: fall back to original preload logic |
| Storage quota exceeded | Installation fails | Low | Check quota before install, warn user |
| iOS evicts cache under pressure | Songs disappear | Medium | Request persistent storage, test on low-storage devices |
| Forgot to regenerate SW after adding songs | Users don't see updates | High | Automate version generation in process_songs.py |
| One corrupted audio file breaks install | App doesn't cache | Medium | Individual audio caching with error handling |
| Update applies during active use | Interrupts playback | Low | User-triggered updates only, banner notification |
| Double-download (preload + SW cache) | 90MB initial download | High | Remove original preload, rely on SW cache |

---

## Open Questions / Decisions Needed

### 1. Splash Screens for iOS
**Question**: Include iOS splash screens for various device sizes?

**Tradeoff**:
- Pro: Nicer loading experience, looks more "native"
- Con: 6-8 additional PNG files (~2-3MB), maintenance burden

**Recommendation**: Skip for MVP, add later if needed.

---

### 2. Split Audio by Team
**Question**: Should varsity.html and jv.html only cache their team's songs?

**Current plan**: Cache all 36 songs regardless of page

**Tradeoff**:
- Current: ~45MB, but all songs always available
- Split: ~25MB per page, but can't switch teams without re-downloading

**Recommendation**: Keep current approach (cache all songs). Teams share many facilities and might need access to both.

---

### 3. Analytics/Monitoring
**Question**: Track PWA usage, installation rate, offline usage?

**Options**:
- A) No analytics - simple, privacy-friendly
- B) LocalStorage-based - privacy-friendly, limited insights
- C) External service - full insights, privacy concerns

**Recommendation**: LocalStorage-based logging for debugging, review after MVP.

---

## Deployment Checklist

Before deploying to production:

- [ ] HTTPS enabled (required for PWA)
- [ ] All paths use relative format (`./`)
- [ ] Manifest.json accessible at root
- [ ] Service worker registered from app.js (not inline scripts)
- [ ] process_songs.py generates sw.js with hash
- [ ] Tested on iOS device in airplane mode
- [ ] Verified cache size ~45-46MB (not 90MB)
- [ ] All 36 songs play offline
- [ ] Update flow tested (add song, see banner, update works)
- [ ] No console errors in production

---

## References

- [MDN: PWA Documentation](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [Google: PWA Checklist](https://web.dev/pwa-checklist/)
- [Apple: Safari Web Apps](https://developer.apple.com/documentation/webkit/safari_web_extensions)
- [Workbox (Google's SW library)](https://developers.google.com/web/tools/workbox) - Consider if hand-rolling SW becomes complex

---

**Status**: Architectural Planning Complete
**Next Step**: Implement Phase 1 (Manifest & Icons)
**Last Updated**: 2026-02-15

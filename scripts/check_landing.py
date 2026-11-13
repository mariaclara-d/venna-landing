"""Browser regression checks. Run against a local HTTP server (default port 8765)."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright

BASE = os.environ.get('VENNA_TEST_URL', 'http://127.0.0.1:8765')
OUT = Path(os.environ.get('TEMP', '/tmp')) / 'venna-qa'
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page()
    page.route('https://connect.facebook.net/**', lambda r: r.fulfill(status=200, content_type='text/javascript', body=''))
    page.route('https://www.facebook.com/**', lambda r: r.abort())
    errors, failures = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: failures.append(f'{r.status} {r.url}') if r.status >= 400 else None)
    results = []
    for width, height in [(320, 740), (375, 812), (390, 844), (430, 932), (768, 1024), (1024, 768), (1440, 900), (1920, 1080)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.goto(BASE, wait_until='networkidle')
        if page.locator('#offer-dialog').is_visible():
            page.locator('.offer-close').click()
        page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
        page.evaluate('document.fonts.ready')
        overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not overflow, f'Horizontal overflow at {width}'
        for section in ['#linhas', '#piscinas', '#contato']:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(150)
        for img in page.locator('img').all():
            if not img.is_visible():
                continue
            img.scroll_into_view_if_needed()
            img.evaluate("el => el.decode()")
            assert img.evaluate('el => el.naturalWidth > 0'), img.get_attribute('src')
        assert page.locator('h1').count() == 1
        assert page.locator('.product-card').count() == 4
        assert page.locator('[data-whatsapp="Pedras naturais"] img').get_attribute('src') == 'img/pedra-moledo-champagne.webp'
        page.evaluate('window.scrollTo(0, 0)')
        page.wait_for_timeout(100)
        page.screenshot(path=str(OUT / f'{width}.png'), full_page=True)
        results.append({'width': width, 'height': height, 'horizontal_overflow': overflow, 'images': 'ok'})

    page.set_viewport_size({'width': 375, 'height': 812})
    page.goto(BASE, wait_until='networkidle')
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
    page.locator('nav a[href="#contato"]').click()
    page.wait_for_timeout(250)
    assert page.locator('.floating-cta').evaluate("el => getComputedStyle(el).visibility === 'hidden'")
    page.locator('#nome').fill('   ')
    page.locator('button[type="submit"]').click()
    assert page.locator('#nome').evaluate('el => !el.validity.valid')
    page.locator('#nome').fill('Maria Teste')
    page.locator('#perfil').select_option(label='Arquiteto(a)')
    page.locator('#interesse').select_option(label='Pedras naturais')
    page.locator('#metragem').fill('25,5')
    destinations = []
    def capture(route):
        destinations.append(route.request.url)
        route.fulfill(status=200, body='WhatsApp destination intercepted by local test.')
    page.route('https://wa.me/**', capture)
    page.locator('button[type="submit"]').click()
    page.wait_for_url('https://wa.me/**')
    message = parse_qs(urlparse(destinations[-1]).query)['text'][0]
    assert 'Maria Teste' in message and '25,5' in message and 'Pedras naturais' in message
    assert '\n' in message and '\\n' not in message
    assert not errors, errors
    assert not failures, failures

    nojs = browser.new_context(java_script_enabled=False, viewport={'width': 375, 'height': 812})
    nojs.route('https://www.facebook.com/**', lambda r: r.abort())
    plain = nojs.new_page()
    plain.goto(BASE)
    assert plain.locator('h1').is_visible()
    assert plain.locator('.product-card').count() == 4
    assert plain.locator('.header-cta').get_attribute('href').startswith('https://wa.me/')
    browser.close()
    report = {'viewports': results, 'javascript_errors': errors, 'http_errors': failures, 'form': 'validations and WhatsApp message passed (navigation intercepted; nothing sent)', 'without_javascript': 'content and contact links available'}
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print(f'Screenshots: {OUT}')

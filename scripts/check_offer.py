"""Verify the campaign modal and links locally, without contacting Meta or WhatsApp."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse
import os
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1] / 'site'
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
out = Path(os.environ['TEMP']) / 'venna-qa'
out.mkdir(exist_ok=True)
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        for width, height in [(320, 568), (390, 844), (768, 1024), (1440, 900), (844, 390)]:
            context = browser.new_context(viewport={'width': width, 'height': height})
            context.route('https://connect.facebook.net/**', lambda r: r.fulfill(status=200, content_type='text/javascript', body=''))
            context.route('https://www.facebook.com/**', lambda r: r.abort())
            context.route('https://wa.me/**', lambda r: r.abort())
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url, wait_until='networkidle')
            modal = page.locator('#offer-dialog')
            assert modal.is_visible(), 'Offer must open immediately'
            for selector in ['.offer-close', '.offer-dialog-actions .button']:
                box = page.locator(selector).bounding_box()
                assert 0 <= box['y'] and box['y'] + box['height'] <= height
                assert 0 <= box['x'] and box['x'] + box['width'] <= width
            page.locator('.offer-art img').evaluate('el => el.decode()')
            page.screenshot(path=str(out / f'offer-{width}.png'))
            page.keyboard.press('Escape')
            assert not modal.is_visible()
            page.wait_for_function("!document.body.classList.contains('offer-open')")
            page.reload(wait_until='networkidle')
            assert not modal.is_visible(), 'Do not repeat in same session'
            page.locator('[data-open-offer]').click()
            assert modal.is_visible()
            page.locator('.offer-dialog-actions a').evaluate("el => el.addEventListener('click', e => e.preventDefault())")
            page.locator('.offer-dialog-actions a').click()
            event = page.evaluate('Array.from(fbq.queue[fbq.queue.length - 1])')
            assert event == ['track', 'Contact', {'contact_method': 'WhatsApp', 'source': 'popup-oferta'}]
            page.locator('.offer-close').click()
            for link in page.locator('[data-whatsapp="oferta"]').all():
                parsed = urlparse(link.get_attribute('href'))
                message = parse_qs(parsed.query)['text'][0]
                assert parsed.path == '/5571981054103'
                assert all(text in message for text in ['Travertino Rockface', '136,99', '50 m²'])
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not errors, errors
            context.close()
        browser.close()
        print('PASS: immediate modal, session frequency, reopening, Escape/close, visible CTA, offer messages, Pixel attribution and responsive layouts.')
finally:
    server.shutdown()
    server.server_close()

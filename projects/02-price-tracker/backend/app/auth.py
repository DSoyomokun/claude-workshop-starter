import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SESSION_PATH = os.environ.get("SESSION_PATH", "grailed_session.json")
GRAILED_LOGIN_URL = "https://www.grailed.com/login"

logger = logging.getLogger(__name__)


def session_exists() -> bool:
    return Path(SESSION_PATH).exists()


async def login_and_save_session():
    """Open a headed browser, let user log in manually, save storageState."""
    from playwright.async_api import async_playwright

    logger.info("Opening browser for Grailed login — log in and close the page when done.")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(GRAILED_LOGIN_URL)

        # Wait until user navigates away from the login page (i.e. successful login)
        try:
            await page.wait_for_url(
                lambda url: "grailed.com" in url and "/login" not in url,
                timeout=120_000,
            )
        except Exception:
            logger.warning("Login wait timed out or was cancelled.")

        await context.storage_state(path=SESSION_PATH)
        logger.info("Session saved to %s", SESSION_PATH)
        await browser.close()


async def get_logged_in_username() -> str | None:
    """Quick headless check — return username if session is valid, else None."""
    if not session_exists():
        return None

    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=SESSION_PATH)
            page = await context.new_page()
            await page.goto("https://www.grailed.com", timeout=15_000)

            # Grailed surfaces username in the nav; fall back to None if not found
            username = await page.evaluate("""
                () => {
                    const el = document.querySelector('[data-cy="username"], .username, [href*="/username"]');
                    return el ? el.textContent.trim().replace('@','') : null;
                }
            """)
            await browser.close()
            return username or "connected"
    except Exception as e:
        logger.error("Session check failed: %s", e)
        return None

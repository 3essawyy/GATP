"""TC-103: documented BookShelf behaviors (fixtures/README.md FX-1…FX-6, FXC-1…FXC-2)."""

from playwright.sync_api import Page, expect


def login(page: Page, base: str, button: str = "Sign in") -> None:
    page.goto(f"{base}/index.html")
    page.get_by_label("Username").fill("tester")
    page.get_by_label("Password").fill("secret123")
    page.get_by_role("button", name=button).click()
    expect(page).to_have_url(f"{base}/books.html")


def test_fx1_valid_login_shows_books(page: Page, site_v1: str) -> None:
    login(page, site_v1)
    expect(page.get_by_role("heading", name="Books")).to_be_visible()
    expect(page.locator("#current-user")).to_have_text("tester")
    expect(page.locator("#result-count")).to_have_text("5 book(s)")


def test_fx2_invalid_login_shows_error(page: Page, site_v1: str) -> None:
    page.goto(f"{site_v1}/index.html")
    page.get_by_label("Username").fill("tester")
    page.get_by_label("Password").fill("wrong")
    page.get_by_test_id("login-submit").click()
    expect(page.get_by_role("alert")).to_have_text("Invalid username or password.")
    expect(page).to_have_url(f"{site_v1}/index.html")


def test_protected_pages_redirect_to_login(page: Page, site_v1: str) -> None:
    page.goto(f"{site_v1}/books.html")
    expect(page).to_have_url(f"{site_v1}/index.html")


def test_fx3_search_by_title_or_author(page: Page, site_v1: str) -> None:
    login(page, site_v1)
    page.get_by_test_id("book-search").fill("butler")
    expect(page.locator("#result-count")).to_have_text("1 book(s)")
    expect(page.get_by_role("cell", name="Kindred")).to_be_visible()
    page.get_by_test_id("book-search").fill("zzz")
    expect(page.get_by_text("No books match your search.")).to_be_visible()


def test_fx4_genre_filter(page: Page, site_v1: str) -> None:
    login(page, site_v1)
    page.locator("#genre-filter").select_option("Fiction")
    expect(page.locator("#result-count")).to_have_text("2 book(s)")


def test_fx5_validation_errors(page: Page, site_v1: str) -> None:
    login(page, site_v1)
    page.get_by_test_id("add-book-link").click()
    page.get_by_placeholder("Year published").fill("1200")
    page.get_by_test_id("save-book").click()
    expect(page.locator("#title-error")).to_have_text("Title is required.")
    expect(page.locator("#author-error")).to_have_text("Author is required.")
    expect(page.locator("#year-error")).to_contain_text("between 1450 and")
    expect(page.locator("#genre-error")).to_have_text("Choose a genre.")
    expect(page).to_have_url(f"{site_v1}/add.html")


def test_fx6_save_adds_book(page: Page, site_v1: str) -> None:
    login(page, site_v1)
    page.get_by_test_id("add-book-link").click()
    page.get_by_label("Title").fill("Dune")
    page.get_by_label("Author").fill("Frank Herbert")
    page.get_by_placeholder("Year published").fill("1965")
    page.get_by_label("Genre").select_option("Fiction")
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_role("status")).to_have_text('Book "Dune" saved.')
    expect(page.locator("#result-count")).to_have_text("6 book(s)")


def test_fxc1_v2_login_button_renamed(page: Page, site_v2: str) -> None:
    page.goto(f"{site_v2}/index.html")
    expect(page.get_by_test_id("login-submit")).to_have_count(0)
    expect(page.get_by_role("button", name="Sign in")).to_have_count(0)
    login(page, site_v2, button="Log in")


def _fill_book(page: Page, title: str) -> None:
    page.get_by_label("Title").fill(title)
    page.get_by_label("Author").fill("Someone")
    page.get_by_placeholder("Year published").fill("2001")
    page.get_by_label("Genre").select_option("Science")


def test_fxc2_v2_save_split_into_draft_and_publish(page: Page, site_v2: str) -> None:
    login(page, site_v2, button="Log in")
    page.get_by_test_id("add-book-link").click()
    expect(page.get_by_test_id("save-book")).to_have_count(0)
    _fill_book(page, "Draft Book")
    page.get_by_role("button", name="Save draft").click()
    expect(page.get_by_role("status")).to_have_text('Draft "Draft Book" saved.')
    draft_row = page.get_by_role("row").filter(has_text="Draft Book")
    expect(draft_row.locator(".badge")).to_have_text("Draft")
    page.get_by_test_id("add-book-link").click()
    _fill_book(page, "Published Book")
    page.get_by_role("button", name="Publish").click()
    expect(page.get_by_role("status")).to_have_text('Book "Published Book" saved.')
    published_row = page.get_by_role("row").filter(has_text="Published Book")
    expect(published_row.locator(".badge")).to_have_count(0)
    expect(page.locator("#result-count")).to_have_text("7 book(s)")

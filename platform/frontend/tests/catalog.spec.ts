import { test, expect } from "@playwright/test";
test("catalog search, technical data and SSR standard page", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "کاتالوگ محصولات" }),
  ).toBeVisible();
  await expect(page.locator(".product-card").first()).toBeVisible();
  await page
    .getByRole("textbox", { name: "جستجوی محصول" })
    .fill("پیچ آلن ۳ در ۲۵ ۸.۸ گالوانیزه");
  await expect(page.locator(".tech-code").first()).toContainText(
    "DIN912-M3X25-8.8-ZN",
  );
  await page
    .locator(".product-card")
    .first()
    .getByRole("button", { name: "مشخصات فنی" })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page
    .getByRole("link", { name: "مشاهدهٔ صفحهٔ استاندارد و جدول‌ها" })
    .click();
  await expect(
    page.getByRole("heading", { name: "DIN912", exact: true }),
  ).toBeVisible();
  await expect(page.locator("table").first()).toBeVisible();
});
test("basket supports selecting and removing actual products", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator(".product-card").first()).toBeVisible();
  const button = page
    .locator(".product-card")
    .first()
    .getByRole("button", { name: /انتخاب/ });
  await button.click();
  await expect(page.locator(".basket-count")).toContainText("1");
  await button.click();
  await expect(page.locator(".basket-count")).toContainText("0");
});
test("keyboard search and modal focus work", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Control+k");
  await expect(
    page.getByRole("textbox", { name: "جستجوی محصول" }),
  ).toBeFocused();
  await page.getByRole("button", { name: /ورود به فضای کارکنان/ }).click();
  await expect(page.getByLabel("نام کاربری")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByLabel("نام کاربری")).not.toBeVisible();
});
test("mobile fits screen and theme persists", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.locator(".product-card").first()).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "تغییر پوسته" }).click();
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator(".product-card").first()).toBeVisible();
  await page.screenshot({
    path: "test-results/mobile-catalog.png",
    fullPage: false,
  });
});

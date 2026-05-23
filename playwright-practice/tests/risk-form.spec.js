const { test, expect } = require("@playwright/test");
const path = require("path");

function getPageUrl() {
  const filePath = path.resolve(__dirname, "../index.html");
  return `file://${filePath}`;
}

test.describe("Risk Signal Form E2E Practice", () => {
  test("low risk input shows INFO and human_required false", async ({ page }) => {
    await page.goto(getPageUrl());

    await page.getByLabel("confidence").fill("0.9");
    await page.getByLabel("latency_ms").fill("800");
    await page.getByLabel("model_version").fill("v1");

    await page.getByRole("button", { name: "Evaluate" }).click();

    await expect(page.getByTestId("level")).toHaveText("INFO");
    await expect(page.getByTestId("risk-score")).toHaveText("0");
    await expect(page.getByTestId("uncertainty-score")).toHaveText("0");
    await expect(page.getByTestId("human-required")).toHaveText("false");
  });

  test("high risk with uncertainty shows WARN and human_required true", async ({ page }) => {
    await page.goto(getPageUrl());

    await page.getByLabel("confidence").fill("0.3");
    await page.getByLabel("latency_ms").fill("2800");
    await page.getByLabel("model_version").fill("");

    await page.getByRole("button", { name: "Evaluate" }).click();

    await expect(page.getByTestId("level")).toHaveText("WARN");
    await expect(page.getByTestId("risk-score")).toHaveText("5");
    await expect(page.getByTestId("uncertainty-score")).toHaveText("1");
    await expect(page.getByTestId("human-required")).toHaveText("true");
  });

  test("high risk with low uncertainty shows CRITICAL and human_required true", async ({ page }) => {
    await page.goto(getPageUrl());

    await page.getByLabel("confidence").fill("0.3");
    await page.getByLabel("latency_ms").fill("2800");
    await page.getByLabel("model_version").fill("v1");

    await page.getByRole("button", { name: "Evaluate" }).click();

    await expect(page.getByTestId("level")).toHaveText("CRITICAL");
    await expect(page.getByTestId("risk-score")).toHaveText("5");
    await expect(page.getByTestId("uncertainty-score")).toHaveText("0");
    await expect(page.getByTestId("human-required")).toHaveText("true");
  });
});
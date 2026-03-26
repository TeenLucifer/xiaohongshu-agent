import { expect, test } from "@playwright/test";

test("renders the chat-first workspace and supports the compact right-side workflow", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "春季通勤穿搭" })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "主导航" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Agent 对话主栏" })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "当前工作区" })).toBeVisible();
  await expect(page.getByRole("list", { name: "对话消息流" })).toBeVisible();
  await expect(page.getByText("第一轮搜集已经完成。")).toBeVisible();
  await expect(page.getByLabel("对话输入框")).toBeVisible();
  await expect(page.getByRole("button", { name: "发送消息" })).toBeVisible();

  const firstImage = page.getByRole("img", { name: "春日通勤西装 3 套搭法 封面图" });
  await expect(firstImage).toBeVisible();
  await expect(firstImage).toHaveAttribute("src", /ScreenShot_2026-03-26_201829_887\.png/);

  await page.getByRole("button", { name: /早八不费力通勤妆 \+ 穿搭/ }).click();
  await expect(page.getByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" })).toBeVisible();
  await page.getByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" }).getByRole("button", { name: "加入已选" }).click();
  await expect(page.getByRole("button", { name: "早八不费力通勤妆 + 穿搭 封面图 早八不费力通勤妆 + 穿搭 3" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "早八不费力通勤妆 + 穿搭" })).not.toBeVisible();

  await page.getByRole("button", { name: "展开文案" }).click();
  await expect(page.getByText("当前文案", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "展开图片" }).click();
  await expect(page.getByRole("heading", { name: "文生图" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "图生图" })).toBeVisible();

  const mainColumn = page.getByTestId("workspace-main-column");
  const contextColumn = page.getByTestId("workspace-context-column");
  const mainBefore = await mainColumn.boundingBox();
  const contextBefore = await contextColumn.boundingBox();

  expect(mainBefore?.width).toBeTruthy();
  expect(contextBefore?.width).toBeTruthy();

  await page.getByRole("button", { name: "收起工作区" }).click();
  await expect(page.getByRole("button", { name: "展开工作区" })).toBeVisible();
  await page.waitForTimeout(350);

  const mainAfter = await mainColumn.boundingBox();
  const contextAfter = await contextColumn.boundingBox();
  expect((mainAfter?.width ?? 0) > (mainBefore?.width ?? 0)).toBeTruthy();
  expect((contextAfter?.width ?? 0) < (contextBefore?.width ?? 0)).toBeTruthy();

  await page.getByRole("button", { name: "展开工作区" }).click();
  await expect(page.getByRole("heading", { name: "搜索结果" })).toBeVisible();
});

test("switches topic from the sidebar and keeps empty states", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: /租房小户型改造/ }).click();

  await expect(page.getByRole("heading", { name: "租房小户型改造" })).toBeVisible();
  await page.getByRole("button", { name: "展开素材" }).click();
  await expect(page.getByText("空状态").first()).toBeVisible();
});

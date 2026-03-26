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
  const sidebar = page.getByTestId("workspace-sidebar");
  const mainBefore = await mainColumn.boundingBox();
  const contextBefore = await contextColumn.boundingBox();
  const sidebarBefore = await sidebar.boundingBox();

  expect(mainBefore?.width).toBeTruthy();
  expect(contextBefore?.width).toBeTruthy();
  expect(sidebarBefore?.width).toBeTruthy();
  expect(sidebarBefore?.x ?? 999).toBeLessThan(4);
  expect(sidebarBefore?.y ?? 999).toBeLessThan(4);
  expect(Math.abs((sidebarBefore?.height ?? 0) - page.viewportSize()!.height)).toBeLessThan(6);

  await page.getByRole("button", { name: "收起侧边栏" }).click();
  await expect(page.getByRole("button", { name: "展开侧边栏" })).toBeVisible();
  await expect(page.getByRole("button", { name: "当前会话" })).toBeVisible();
  await expect(page.getByRole("button", { name: "历史记录" })).toBeVisible();
  await page.waitForTimeout(350);

  const mainAfterLeftCollapse = await mainColumn.boundingBox();
  const contextAfterLeftCollapse = await contextColumn.boundingBox();
  const sidebarAfterLeftCollapse = await sidebar.boundingBox();

  expect(Math.abs((mainAfterLeftCollapse?.width ?? 0) - (mainBefore?.width ?? 0))).toBeLessThan(6);
  expect((contextAfterLeftCollapse?.width ?? 0) > (contextBefore?.width ?? 0)).toBeTruthy();
  expect((sidebarAfterLeftCollapse?.width ?? 0) < (sidebarBefore?.width ?? 0)).toBeTruthy();

  await page.getByRole("button", { name: "展开侧边栏" }).click();
  await page.getByRole("button", { name: "收起工作区" }).click();
  await expect(page.getByRole("button", { name: "展开工作区" })).toBeVisible();
  await page.waitForTimeout(350);

  const mainAfterRightCollapse = await mainColumn.boundingBox();
  const contextAfterRightCollapse = await contextColumn.boundingBox();

  await page.getByRole("button", { name: "收起侧边栏" }).click();
  await expect(page.getByRole("button", { name: "展开侧边栏" })).toBeVisible();
  await page.waitForTimeout(350);

  const mainAfterBothCollapse = await mainColumn.boundingBox();
  const contextAfterBothCollapse = await contextColumn.boundingBox();

  expect(Math.abs((mainAfterBothCollapse?.width ?? 0) - (mainAfterRightCollapse?.width ?? 0))).toBeLessThan(6);
  expect(Math.abs((contextAfterBothCollapse?.width ?? 0) - (contextAfterRightCollapse?.width ?? 0))).toBeLessThan(6);

  await page.getByRole("button", { name: "展开工作区" }).click();
  await page.getByRole("button", { name: "展开侧边栏" }).click();
  await expect(page.getByRole("heading", { name: "搜索结果" })).toBeVisible();
});

test("switches topic from the sidebar and keeps empty states", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: /租房小户型改造/ }).click();

  await expect(page.getByRole("heading", { name: "租房小户型改造" })).toBeVisible();
  await page.getByRole("button", { name: "展开素材" }).click();
  await expect(page.getByText("空状态").first()).toBeVisible();
});

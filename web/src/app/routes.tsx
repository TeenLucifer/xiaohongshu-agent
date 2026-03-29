import { Route, Routes } from "react-router-dom";
import { TopicListPage } from "./TopicListPage";
import { TopicWorkspacePage } from "./TopicWorkspacePage";

export function AppRoutes(): JSX.Element {
  return (
    <Routes>
      <Route element={<TopicListPage />} path="/" />
      <Route element={<TopicListPage />} path="/topics" />
      <Route element={<TopicWorkspacePage />} path="/topics/:topicId" />
    </Routes>
  );
}

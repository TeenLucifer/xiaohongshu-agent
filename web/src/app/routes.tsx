import { Route, Routes } from "react-router-dom";
import { TopicWorkspacePage } from "./TopicWorkspacePage";

export function AppRoutes(): JSX.Element {
  return (
    <Routes>
      <Route element={<TopicWorkspacePage />} path="/" />
      <Route element={<TopicWorkspacePage />} path="/topics/:topicId" />
    </Routes>
  );
}

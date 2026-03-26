import { BrowserRouter } from "react-router-dom";
import { AppRoutes } from "./routes";

export function App(): JSX.Element {
  return (
    <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <AppRoutes />
    </BrowserRouter>
  );
}

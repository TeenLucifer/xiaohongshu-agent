import type { SectionStatus } from "../types/workspace";

const statusLabelMap: Record<SectionStatus, string> = {
  empty: "空状态",
  loading: "加载中",
  success: "展示中",
  error: "错误"
};

export function StatusBadge({ status }: { status: SectionStatus }): JSX.Element {
  return (
    <span className={`status-badge status-${status}`} aria-label={`当前状态：${statusLabelMap[status]}`}>
      {statusLabelMap[status]}
    </span>
  );
}

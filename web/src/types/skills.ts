export interface SkillListItem {
  name: string;
  description: string;
  source: string;
  location: string;
  available: boolean;
  requires: string[];
  contentSummary: string;
}

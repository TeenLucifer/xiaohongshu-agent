import { Link } from "react-router-dom";
import { mockTopics } from "../data/mockTopics";

export function TopicListPage(): JSX.Element {
  return (
    <main className="page-shell">
      <header className="page-header">
        <p className="eyebrow">Frontend Feature 001</p>
        <h1>话题工作台</h1>
        <p className="page-description">先用 Mock 数据固定话题列表页和单话题工作台页的前端结构。</p>
      </header>

      <section className="topic-grid" aria-label="话题列表">
        {mockTopics.map((topic) => {
          return (
            <Link className="topic-card" key={topic.id} to={`/topics/${topic.id}`}>
              <div className="topic-card-meta">
                <span>最近更新</span>
                <strong>{topic.updatedAt}</strong>
              </div>
              <h2>{topic.title}</h2>
              <p>{topic.description}</p>
              <span className="topic-card-action">进入工作台</span>
            </Link>
          );
        })}
      </section>
    </main>
  );
}

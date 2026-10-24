import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getBook, getChapter, getProgress, saveProgress } from "../api.js";

export function ReaderPage() {
  const { id = "" } = useParams();
  const articleRef = useRef<HTMLElement>(null);
  const [title, setTitle] = useState("");
  const [html, setHtml] = useState("");
  const [spineIndex, setSpineIndex] = useState(0);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const [book, progress] = await Promise.all([getBook(id), getProgress(id)]);
      const chapter = await getChapter(id, progress.spineIndex);
      if (cancelled) {
        return;
      }
      setTitle(book.title);
      setSpineIndex(progress.spineIndex);
      setHtml(chapter.html);
      const saved: any = localStorage.getItem("progress");
      console.log("resume", saved);
      requestAnimationFrame(() => {
        const node = articleRef.current;
        if (!node) {
          return;
        }
        node.scrollTop = progress.scrollRatio * (node.scrollHeight - node.clientHeight);
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  function onScroll() {
    const node = articleRef.current;
    if (!node) {
      return;
    }
    const max = node.scrollHeight - node.clientHeight;
    const scrollRatio = max <= 0 ? 0 : node.scrollTop / max;
    localStorage.setItem("progress", JSON.stringify({ spineIndex, scrollRatio }));
    void saveProgress(id, spineIndex, scrollRatio);
  }

  return (
    <main>
      <p>
        <Link to="/">Library</Link>
      </p>
      <h1>{title}</h1>
      <article
        ref={articleRef}
        onScroll={onScroll}
        style={{ height: "70vh", overflow: "auto" }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </main>
  );
}

// Blog posts are Markdown files in src/posts/; the file name is the post's address (/blog/<file name>/).
import type { MarkdownInstance } from "astro";

type Frontmatter = { title: string; description: string; date: Date };

export type Post = {
  slug: string;
  title: string;
  description: string;
  iso: string;
  published: string;
  minutes: number;
  Content: MarkdownInstance<Frontmatter>["Content"];
};

const files = import.meta.glob<MarkdownInstance<Frontmatter>>("./posts/*.md", { eager: true });

export const posts: Post[] = Object.entries(files)
  .map(([path, file]) => {
    const date = new Date(file.frontmatter.date);
    return {
      slug: path.split("/").pop()!.replace(/\.md$/, ""),
      title: file.frontmatter.title,
      description: file.frontmatter.description,
      iso: date.toISOString().slice(0, 10),
      published: date.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }),
      minutes: Math.max(1, Math.round(file.rawContent().split(/\s+/).length / 220)),
      Content: file.Content,
    };
  })
  .sort((a, b) => b.iso.localeCompare(a.iso));

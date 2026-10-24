import { XMLParser } from "fast-xml-parser";
import JSZip from "jszip";

export type ParsedEpub = {
  title: string;
  authors: string[];
  spine: string[];
};

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  removeNSPrefix: true,
});

function asArray<T>(value: T | T[] | undefined): T[] {
  if (value === undefined) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}

function textOf(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (value && typeof value === "object" && "#text" in value) {
    const text = (value as { "#text": unknown })["#text"];
    return typeof text === "string" ? text : "";
  }
  return "";
}

export async function parseEpub(bytes: Buffer): Promise<ParsedEpub> {
  const zip = await JSZip.loadAsync(bytes);
  const containerXml = await zip.file("META-INF/container.xml")?.async("string");
  if (!containerXml) {
    throw new Error("Missing META-INF/container.xml");
  }
  const container = parser.parse(containerXml) as {
    container?: { rootfiles?: { rootfile?: { "@_full-path"?: string } } };
  };
  const opfPath = container.container?.rootfiles?.rootfile?.["@_full-path"];
  if (!opfPath) {
    throw new Error("Missing OPF path");
  }
  const opfXml = await zip.file(opfPath)?.async("string");
  if (!opfXml) {
    throw new Error("Missing OPF");
  }
  const opf = parser.parse(opfXml) as {
    package?: {
      metadata?: { title?: unknown; creator?: unknown };
      manifest?: { item?: unknown };
      spine?: { itemref?: unknown };
    };
  };
  const metadata = opf.package?.metadata ?? {};
  const title = textOf(metadata.title) || "Untitled";
  const authors = asArray(metadata.creator)
    .map((item) => textOf(item))
    .filter((name) => name.length > 0);
  const items = asArray(opf.package?.manifest?.item as { "@_id"?: string; "@_href"?: string }[]);
  const hrefById = new Map(
    items.flatMap((item) => {
      if (item["@_id"] && item["@_href"]) {
        return [[item["@_id"], item["@_href"]] as const];
      }
      return [];
    }),
  );
  const base = opfPath.includes("/") ? opfPath.slice(0, opfPath.lastIndexOf("/") + 1) : "";
  const spine = asArray(opf.package?.spine?.itemref as { "@_idref"?: string }[])
    .map((ref) => ref["@_idref"])
    .filter((id): id is string => Boolean(id))
    .map((id) => hrefById.get(id))
    .filter((href): href is string => Boolean(href))
    .map((href) => (href.startsWith("/") ? href.slice(1) : `${base}${href}`));
  return { title, authors, spine };
}

export async function readChapter(bytes: Buffer, href: string): Promise<string> {
  const zip = await JSZip.loadAsync(bytes);
  const html = await zip.file(href)?.async("string");
  if (!html) {
    throw new Error(`Missing chapter ${href}`);
  }
  return html;
}

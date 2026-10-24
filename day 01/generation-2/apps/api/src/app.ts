import cors from "@fastify/cors";
import multipart from "@fastify/multipart";
import Fastify, { type FastifyInstance } from "fastify";
import { BookNotFoundError, Library } from "./library.js";

export async function buildApp(library: Library): Promise<FastifyInstance> {
  const app = Fastify();
  await app.register(cors);
  await app.register(multipart);

  app.get("/books", async (request) => {
    const { q } = request.query as { q?: string };
    return library.list(q);
  });

  app.post("/books", async (request, reply) => {
    const file = await request.file();
    if (!file) {
      return reply.code(400).send({ error: "file required" });
    }
    const bytes = await file.toBuffer();
    const book = await library.addEpub(bytes);
    return reply.code(201).send(book);
  });

  app.get("/books/:id", async (request, reply) => {
    const { id } = request.params as { id: string };
    try {
      return library.get(id);
    } catch (error) {
      if (error instanceof BookNotFoundError) {
        return reply.code(404).send({ error: "not found" });
      }
      throw error;
    }
  });

  app.get("/books/:id/chapters/:index", async (request, reply) => {
    const { id, index } = request.params as { id: string; index: string };
    try {
      return await library.chapter(id, Number(index));
    } catch (error) {
      if (error instanceof BookNotFoundError) {
        return reply.code(404).send({ error: "not found" });
      }
      throw error;
    }
  });

  app.get("/books/:id/progress", async (request, reply) => {
    const { id } = request.params as { id: string };
    try {
      return library.progressFor(id);
    } catch (error) {
      if (error instanceof BookNotFoundError) {
        return reply.code(404).send({ error: "not found" });
      }
      throw error;
    }
  });

  app.put("/books/:id/progress", async (request, reply) => {
    const { id } = request.params as { id: string };
    const body = request.body as { spineIndex?: number; scrollRatio?: number };
    try {
      return library.saveProgress(id, body.spineIndex ?? 0, body.scrollRatio ?? 0);
    } catch (error) {
      if (error instanceof BookNotFoundError) {
        return reply.code(404).send({ error: "not found" });
      }
      throw error;
    }
  });

  return app;
}

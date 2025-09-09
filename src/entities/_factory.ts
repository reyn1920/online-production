// src/entities/_factory.ts
import { uid, put, get as getOne, del, all } from './_db';

type Sort = string | undefined; // "-created_at" or "created_at"
type Filter = (row: any) => boolean;

function sortRows(rows: any[], sort?: Sort) {
  if (!sort) return rows;
  const desc = sort.startsWith('-');
  const key = desc ? sort.slice(1) : sort;
  return rows.sort((a, b) => {
    const av = a[key];
    const bv = b[key];
    if (av === bv) return 0;
    return (av > bv ? 1 : -1) * (desc ? -1 : 1);
  });
}

export function makeEntity<T extends object>(store: string) {
  return class Entity {
    static async list(
      sort?: Sort,
      limit?: number,
      filter?: Filter
    ): Promise<(T & { id: string })[]> {
      const rows = await all(store);
      const filtered = filter ? rows.filter(filter) : rows;
      const sorted = sortRows(filtered, sort);
      return (limit ? sorted.slice(0, limit) : sorted) as any;
    }

    static async get(id: string): Promise<(T & { id: string }) | null> {
      return (await getOne(store, id)) as any;
    }

    static async create(data: Partial<T>): Promise<string> {
      const id = uid(store);
      const now = new Date().toISOString();
      const record = { id, ...data, _created_at: now, _updated_at: now };
      await put(store, record);
      return id;
    }

    static async update(id: string, patch: Partial<T>): Promise<void> {
      const curr = await getOne(store, id);
      if (!curr) throw new Error(`${store}: record not found: ${id}`);
      const now = new Date().toISOString();
      await put(store, { ...curr, ...patch, _updated_at: now });
    }

    static async delete(id: string): Promise<void> {
      await del(store, id);
    }
  };
}

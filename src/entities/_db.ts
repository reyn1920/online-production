// src/entities/_db.ts
// Tiny, dependency-free IndexedDB layer with strict schemas + sane errors.

type IndexDef = { name: string; keyPath: string; options?: IDBIndexParameters };
type StoreDef = { name: string; keyPath: string; indexes?: IndexDef[] };

const DB_NAME = 'vidscript_pro_db';
const DB_VERSION = 3;

const STORES: StoreDef[] = [
  {
    name: 'ResearchResult',
    keyPath: 'id',
    indexes: [{ name: 'generated_at', keyPath: 'generated_at' }],
  },
  {
    name: 'YouTubeIntelligence',
    keyPath: 'id',
    indexes: [{ name: 'discovery_date', keyPath: 'discovery_date' }],
  },
  {
    name: 'MarketOpportunity',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'StrategicDecision',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'ViralThumbnailStrategy',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'ViralCopywritingStrategy',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'ViralResearchEngine',
    keyPath: 'id',
    indexes: [{ name: 'research_date', keyPath: 'research_date' }],
  },
  {
    name: 'ViralTrendTracker',
    keyPath: 'id',
    indexes: [{ name: 'first_detected', keyPath: 'first_detected' }],
  },
  {
    name: 'StyleAnalysis',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'ContentPersonality',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'ConservativeStyleGuide',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'ConservativeContentDatabase',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'ConservativeFactDatabase',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'PoliticalSafetyDatabase',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  {
    name: 'MediaBiasDatabase',
    keyPath: 'id',
    indexes: [{ name: 'created_date', keyPath: 'created_date' }],
  },
  { name: 'VideoProject', keyPath: 'id', indexes: [{ name: 'status', keyPath: 'status' }] },
  { name: 'Job', keyPath: 'id', indexes: [{ name: 'status', keyPath: 'status' }] },
  { name: 'Channel', keyPath: 'id', indexes: [{ name: 'status', keyPath: 'status' }] },
  {
    name: 'ABTestCampaign',
    keyPath: 'id',
    indexes: [{ name: 'test_status', keyPath: 'test_status' }],
  },
  { name: 'AdCampaignOptimizer', keyPath: 'id' },
  { name: 'AdCreativeGenerator', keyPath: 'id' },
  { name: 'AdMarketResearch', keyPath: 'id' },
  { name: 'AdSalesAutomation', keyPath: 'id' },
  { name: 'AdaptationRule', keyPath: 'id' },
  {
    name: 'AffiliateProgram',
    keyPath: 'id',
    indexes: [{ name: 'application_status', keyPath: 'application_status' }],
  },
];

let _dbPromise: Promise<IDBDatabase> | null = null;

function openDB(): Promise<IDBDatabase> {
  if (_dbPromise) return _dbPromise;
  _dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      STORES.forEach(def => {
        if (!db.objectStoreNames.contains(def.name)) {
          const store = db.createObjectStore(def.name, { keyPath: def.keyPath });
          def.indexes?.forEach(idx => store.createIndex(idx.name, idx.keyPath, idx.options));
        } else {
          // ensure indexes exist after version bumps
          const store = req.transaction!.objectStore(def.name);
          def.indexes?.forEach(idx => {
            if (!store.indexNames.contains(idx.name)) {
              store.createIndex(idx.name, idx.keyPath, idx.options);
            }
          });
        }
      });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return _dbPromise;
}

export async function tx(store: string, mode: IDBTransactionMode) {
  const db = await openDB();
  return db.transaction(store, mode).objectStore(store);
}

export function uid(prefix = 'id'): string {
  return `${prefix}_${Math.random().toString(36).slice(2)}_${Date.now().toString(36)}`;
}

export async function put(store: string, value: any) {
  const s = await tx(store, 'readwrite');
  return new Promise<void>((resolve, reject) => {
    const req = s.put(value);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function get(store: string, id: string) {
  const s = await tx(store, 'readonly');
  return new Promise<any>((resolve, reject) => {
    const req = s.get(id);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror = () => reject(req.error);
  });
}

export async function del(store: string, id: string) {
  const s = await tx(store, 'readwrite');
  return new Promise<void>((resolve, reject) => {
    const req = s.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function all(store: string): Promise<any[]> {
  const s = await tx(store, 'readonly');
  return new Promise<any[]>((resolve, reject) => {
    const req = s.getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

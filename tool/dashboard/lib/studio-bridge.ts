import type { Character } from "@/lib/repositories";

/** Nhân vật chờ được thả lên canvas Studio (trang Nhân vật ghi, trang Studio đọc). */
const KEY = "studio.pendingCharacters";

export function queueCharacterForStudio(c: Character): void {
  try {
    const list: Character[] = JSON.parse(localStorage.getItem(KEY) || "[]");
    list.push(c);
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    // localStorage không khả dụng: bỏ qua, người dùng vẫn thêm được từ thanh công cụ Studio
  }
}

export function takeQueuedCharacters(): Character[] {
  try {
    const list: Character[] = JSON.parse(localStorage.getItem(KEY) || "[]");
    localStorage.removeItem(KEY);
    return list;
  } catch {
    return [];
  }
}

import fs from "fs";
import path from "path";

const root = path.resolve("tool/dashboard");

function patch(relPath, fn) {
  const full = path.join(root, relPath);
  let src = fs.readFileSync(full, "utf-8");
  const res = fn(src);
  if (src !== res) {
    fs.writeFileSync(full, res, "utf-8");
    console.log(`Updated ${relPath}`);
  } else {
    console.log(`No change for ${relPath}`);
  }
}

// 1. JobsCostTab.tsx
patch("components/studio/tabs/JobsCostTab.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { showAlert } from "@/lib/confirm";');
  }
  return s.replace(
    'alert(`Huỷ job thất bại: ${err.message}`);',
    'await showAlert("Huỷ job thất bại", err.message, "danger");'
  );
});

// 2. SophisticatedChatInput.tsx
patch("components/studio/chat/SophisticatedChatInput.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { showAlert } from "@/lib/confirm";');
  }
  return s.replace(
    'alert(isVi ? "Trình duyệt chưa hỗ trợ ghi âm trực tiếp." : "Speech recognition not supported in this browser.");',
    'showAlert("Ghi âm giọng nói", isVi ? "Trình duyệt chưa hỗ trợ ghi âm trực tiếp." : "Speech recognition not supported in this browser.", "warning");'
  );
});

// 3. CalendarView.tsx
patch("components/social/CalendarView.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { showAlert } from "@/lib/confirm";');
  }
  return s.replace(
    'alert(`Không thể đổi lịch: ${err.message}`);',
    'await showAlert("Không thể đổi lịch", err.message, "danger");'
  );
});

// 4. AccountDetailSheet.tsx
patch("components/social/AccountDetailSheet.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { confirm, showAlert } from "@/lib/confirm";');
  }
  s = s.replace('alert("Vui lòng điền Handle và Tên hiển thị");', 'await showAlert("Thiếu thông tin", "Vui lòng điền Handle và Tên hiển thị", "warning");');
  s = s.replace('alert("Đã đạt giới hạn tối đa 10 tài khoản");', 'await showAlert("Giới hạn tài khoản", "Đã đạt giới hạn tối đa 10 tài khoản", "warning");');
  s = s.replace('alert(`Lỗi lưu tài khoản: ${err.message}`);', 'await showAlert("Lỗi lưu tài khoản", err.message, "danger");');
  s = s.replace(
    'if (confirm(`Bạn có chắc chắn muốn xóa tài khoản ${account.display_name}?`)) {',
    'if (await confirm({ tone: "danger", title: "Xóa tài khoản", message: `Bạn có chắc chắn muốn xóa tài khoản ${account.display_name}?` })) {'
  );
  s = s.replace('alert(`Lỗi xóa tài khoản: ${err.message}`);', 'await showAlert("Lỗi xóa tài khoản", err.message, "danger");');
  return s;
});

// 5. PublishCenterModal.tsx
patch("components/social/PublishCenterModal.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { showAlert } from "@/lib/confirm";');
  }
  s = s.replace('alert(`Lỗi sinh caption: ${err.message}`);', 'await showAlert("Lỗi sinh caption", err.message, "danger");');
  s = s.replace('alert(`Lỗi xem trước lịch: ${err.message}`);', 'await showAlert("Lỗi xem trước lịch", err.message, "danger");');
  s = s.replace('alert(`Lỗi lưu lịch xuất bản: ${err.message}`);', 'await showAlert("Lỗi lưu lịch xuất bản", err.message, "danger");');
  s = s.replace('alert("Tối đa chọn 10 tài khoản");', 'showAlert("Giới hạn tài khoản", "Tối đa chọn 10 tài khoản", "warning");');
  return s;
});

// 6. PostComposer.tsx
patch("components/social/PostComposer.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { confirm } from "@/lib/confirm";');
  }
  return s.replace(
    'if (!window.confirm("Bạn có chắc chắn muốn ĐĂNG NGAY lên các tài khoản đã chọn?")) {',
    'if (!(await confirm({ tone: "warning", title: "Xác nhận đăng bài", message: "Bạn có chắc chắn muốn ĐĂNG NGAY lên các tài khoản đã chọn?" }))) {'
  );
});

// 7. PostRow.tsx
patch("components/social/PostRow.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { confirm } from "@/lib/confirm";');
  }
  s = s.replace(
    'onClick={() => {\n                  setMenuOpen(false);\n                  if (confirm(`Xác nhận đăng bài "${item.title}" lên ${item.account_name} ngay bây giờ?`)) {',
    'onClick={async () => {\n                  setMenuOpen(false);\n                  const ok = await confirm({ tone: "info", title: "Đăng bài ngay", message: `Xác nhận đăng bài "${item.title}" lên ${item.account_name} ngay bây giờ?` });\n                  if (ok) {'
  );
  s = s.replace(
    'onClick={() => {\r\n                  setMenuOpen(false);\r\n                  if (confirm(`Xác nhận đăng bài "${item.title}" lên ${item.account_name} ngay bây giờ?`)) {',
    'onClick={async () => {\r\n                  setMenuOpen(false);\r\n                  const ok = await confirm({ tone: "info", title: "Đăng bài ngay", message: `Xác nhận đăng bài "${item.title}" lên ${item.account_name} ngay bây giờ?` });\r\n                  if (ok) {'
  );
  s = s.replace(
    'onClick={() => {\n                  setMenuOpen(false);\n                  if (confirm(`Hủy lịch đăng bài "${item.title}" trên ${item.account_name}?`)) {',
    'onClick={async () => {\n                  setMenuOpen(false);\n                  const ok = await confirm({ tone: "danger", title: "Hủy lịch đăng bài", message: `Hủy lịch đăng bài "${item.title}" trên ${item.account_name}?` });\n                  if (ok) {'
  );
  s = s.replace(
    'onClick={() => {\r\n                  setMenuOpen(false);\r\n                  if (confirm(`Hủy lịch đăng bài "${item.title}" trên ${item.account_name}?`)) {',
    'onClick={async () => {\r\n                  setMenuOpen(false);\r\n                  const ok = await confirm({ tone: "danger", title: "Hủy lịch đăng bài", message: `Hủy lịch đăng bài "${item.title}" trên ${item.account_name}?` });\r\n                  if (ok) {'
  );
  return s;
});

// 8. AccountsView.tsx
patch("components/social/hub/Accounts/AccountsView.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { confirm } from "@/lib/confirm";');
  }
  return s.replace(
    'if (!confirm(`Bạn có chắc muốn xóa kênh "${accName}" khỏi danh sách tài khoản?`)) return;',
    'if (!(await confirm({ tone: "danger", title: "Xóa tài khoản", message: `Bạn có chắc muốn xóa kênh "${accName}" khỏi danh sách tài khoản?` }))) return;'
  );
});

// 9. QueueView.tsx
patch("components/social/hub/Queue/QueueView.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { confirm } from "@/lib/confirm";');
  }
  s = s.replace(
    'if (!confirm(`Bạn có chắc muốn hủy ${selectedTargetIds.length} bài đăng đã chọn?`)) return;',
    'if (!(await confirm({ tone: "danger", title: "Hủy bài đăng", message: `Bạn có chắc muốn hủy ${selectedTargetIds.length} bài đăng đã chọn?` }))) return;'
  );
  s = s.replace(
    'if (!confirm(`Bạn có chắc muốn xóa vĩnh viễn ${selectedTargetIds.length} bản nháp đã chọn?`)) return;',
    'if (!(await confirm({ tone: "danger", title: "Xóa bản nháp", message: `Bạn có chắc muốn xóa vĩnh viễn ${selectedTargetIds.length} bản nháp đã chọn?` }))) return;'
  );
  return s;
});

// 10. TemplatesView.tsx
patch("components/social/hub/Templates/TemplatesView.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { confirm } from "@/lib/confirm";');
  }
  return s.replace(
    'if (!confirm(`Bạn có chắc muốn xóa mẫu "${title}"?`)) return;',
    'if (!(await confirm({ tone: "danger", title: "Xóa mẫu", message: `Bạn có chắc muốn xóa mẫu "${title}"?` }))) return;'
  );
});

// 11. DetailDrawer.tsx
patch("components/social/hub/common/DetailDrawer.tsx", (s) => {
  if (!s.includes('from "@/lib/confirm"')) {
    s = s.replace('"use client";', '"use client";\nimport { confirm } from "@/lib/confirm";');
  }
  return s.replace(
    'if (!confirm("Bạn có chắc chắn muốn hủy bài đăng này?")) return;',
    'if (!(await confirm({ tone: "danger", title: "Hủy bài đăng", message: "Bạn có chắc chắn muốn hủy bài đăng này?" }))) return;'
  );
});

console.log("Alert and confirm patches applied.");

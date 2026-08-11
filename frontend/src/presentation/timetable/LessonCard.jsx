import { memo, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { PROBLEM_META } from "../../adapters/problemInbox";

const FALLBACK_COLOR = {
  GUEST: { bg: "#fffbeb", border: "#f59e0b", text: "#92400e" },
  RESIDENT: { bg: "#eff6ff", border: "#3b82f6", text: "#1e40af" },
};

// Theo yeu cau: thay the day-chu-luon-hien bang 1 THANH MAU gon (toi uu dien
// tich) - chi hien CHI TIET DAY DU khi di chuot vao, qua popup dinh vi
// position:fixed (portal vao document.body, tranh bi .schedv2-grid-wrap
// overflow-x:auto cat mat). Bam vao thanh se "GIU" popup mo (khong tu dong
// dong khi roi chuot) - can thiet vi thanh qua mong, di chuot tu thanh sang
// popup de bam nut "Tu choi" de mat vi khoang ho giua 2 vung hover. Bam lai
// (hoac bam nut X trong popup) de dong. 2 kenh mau van tach rieng: nen thanh
// mau = phan loai (groupColor tu LessonGridBoard), vien do khi highlighted =
// canh bao, luon de len tren khong doi mau nen.
const LessonCard = memo(function LessonCard({
  lesson, isHighlighted, onClearOverride, groupColor, onPickProblem, detailed = false,
  canDrag = false, onDragStart, onDragEnd,
}) {
  const problems = lesson.problems ?? [];
  const barRef = useRef(null);
  const [hover, setHover] = useState(false);
  const [locked, setLocked] = useState(false);
  const [rect, setRect] = useState(null);
  const [flipLeft, setFlipLeft] = useState(false);

  // Ma lop hoc phan (vd "CSE3003-1") de nhan dien lop - de hon "#<id noi bo>"
  // von khong noi len gi voi giao vu. Fallback ve #id khi lop nao do khong tra
  // duoc ma (khong nen xay ra, nhung tranh hien "undefined").
  const label = lesson.classCode || `#${lesson.id}`;
  const isGuest = lesson.teacherType === "GUEST";
  const color = groupColor || FALLBACK_COLOR[isGuest ? "GUEST" : "RESIDENT"];

  const measure = () => {
    if (!barRef.current) return;
    const r = barRef.current.getBoundingClientRect();
    // Neu thanh da cuon ra ngoai man hinh hoan toan, dong popup luon - de no
    // "troi" o mep man hinh khong con tro toi dau ca thi vo nghia hon.
    if (r.bottom < 0 || r.top > window.innerHeight) {
      setHover(false);
      setLocked(false);
      return;
    }
    setRect(r);
    setFlipLeft(window.innerWidth - r.right < 340);
  };
  const showPopover = () => { measure(); setHover(true); };
  const hidePopover = () => setHover(false);
  const toggleLock = () => {
    measure();
    setLocked((l) => !l);
  };

  const visible = hover || locked;

  // Dong popover NGAY khi bat dau keo - neu khong, popup mo tu truoc (do hover
  // hoac da bam giu) se troi lai giua man hinh trong luc the dang duoc keo di,
  // che khuat luoi va gay roi mat (dung 1 tay keo, 1 tay khong the tu di chuot
  // ra khoi the de trigger onMouseLeave truoc).
  const handleDragStart = (e) => {
    setHover(false);
    setLocked(false);
    onDragStart?.(e);
  };

  // Popup dung position:fixed (theo viewport) de thoat khoi overflow-x:auto
  // cua .schedv2-grid-wrap, nhung vi vay KHONG tu troi theo khi cuon trang -
  // phai tu do lai vi tri moi lan cuon (dung capture:true de bat duoc ca
  // scroll cua cac vung con cuon rieng, khong chi window).
  useEffect(() => {
    if (!visible) return;
    const onScrollOrResize = () => measure();
    window.addEventListener("scroll", onScrollOrResize, true);
    window.addEventListener("resize", onScrollOrResize);
    return () => {
      window.removeEventListener("scroll", onScrollOrResize, true);
      window.removeEventListener("resize", onScrollOrResize);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  // KHONG con gan "dimmed" theo phase (truoc day moi buoi GD1 bi mo di vinh
  // vien mot khi da hien trong trang gop, trong luc no van keo-tha binh
  // thuong duoc - nhin nhu khoa nhung thuc ra khong khoa, mau thuan voi
  // hanh vi thuc).
  const barClass = [
    "lesson-bar",
    detailed ? "detailed" : "",
    isHighlighted ? "highlighted" : "",
    lesson.pendingSave ? "pending-save" : "",
  ]
    .filter(Boolean)
    .join(" ");

  // O che do chi tiet the rong co dinh 180px nen chua duoc chu. Vien trai giu mau
  // phan loai, nen the sang mau nhat cua chinh mau do de chu doc duoc.
  // Vien phai thay duoc ro: nen the rat nhat (color.bg) tren nen luoi trang thi
  // gan nhu khong thay ranh gioi. Dung chinh mau phan loai lam vien mong quanh
  // the + soc day ben trai.
  const detailStyle = detailed
    ? {
        background: color.bg,
        border: `1px solid ${color.border}`,
        borderLeft: `4px solid ${color.border}`,
        color: color.text,
      }
    : { background: color.border };

  return (
    <>
      <div
        ref={barRef}
        className={barClass}
        style={{ ...detailStyle, cursor: canDrag ? "grab" : undefined }}
        data-short={detailed ? String(lesson.duration || 1) : undefined}
        draggable={canDrag}
        onDragStart={canDrag ? handleDragStart : undefined}
        onDragEnd={canDrag ? onDragEnd : undefined}
        // Tooltip he thong: doc duoc ngay ca truoc khi popover kip hien, va la
        // duong doc du phong khi khong dung duoc chuot.
        title={
          problems.length > 0
            ? `${label} ${lesson.courseName} — ${problems
                .map((p) => PROBLEM_META[p.type].label)
                .join(", ")}`
            : `${label} ${lesson.courseName}`
        }
        onMouseEnter={showPopover}
        onMouseLeave={hidePopover}
        onClick={toggleLock}
      >
        {detailed && (
          <span className="lb-body">
            {/* Toan bo thong tin dong thanh MOT KHOI o dinh the. Truoc day ten GV
                bi day xuong day (margin-top:auto) nen the 3 tiet co mot khoang
                trong lon o giua - nhin nhu loi chu khong nhu chu y. */}
            <span className="lb-top">
              <span className="lb-code">
                {label}
                {lesson.isPinned && <span className="lb-pin" aria-label="đã ghim">📌</span>}
                {problems.length > 0 && <span className="lb-warn" aria-label="có vấn đề">!</span>}
              </span>
              <span className="lb-room">{lesson.roomType}</span>
            </span>
            <span className="lb-course">{lesson.courseName}</span>
            <span className="lb-teacher">{lesson.teacherName}</span>
            {/* Neo o day the: giai thich vi sao the cao chung nay. */}
            <span className="lb-dur">{lesson.duration || 1} tiết</span>
          </span>
        )}
      </div>
      {visible && rect && createPortal(
        <div
          className={`lesson-popover ${flipLeft ? "flip-left" : ""}`}
          style={{
            top: rect.top + rect.height / 2,
            left: flipLeft ? undefined : rect.right + 10,
            right: flipLeft ? window.innerWidth - rect.left + 10 : undefined,
            transform: "translateY(-50%)",
          }}
          onMouseEnter={showPopover}
          onMouseLeave={hidePopover}
        >
          {locked && (
            <button type="button" className="tt-close-btn" onClick={() => setLocked(false)} aria-label="Đóng">×</button>
          )}
          <div className="tt-row-top">
            <span className="tt-major" style={{ background: color.bg, color: color.text }}>
              {isGuest ? "THỈNH GIẢNG" : "CƠ HỮU"}
            </span>
            <span className="tt-section">{label}</span>
            {/* Truoc day co them badge "[da chot GD1]" o day, nhung no LUON
                trung voi pill THINH GIANG/CO HUU ngay ben canh (moi buoi
                thinh giang la GD1, moi buoi co huu la GD2 - khong co truong
                hop khac) nen la thong tin lap lai, da bo. */}
            {lesson.isCoTeaching && <span className="lesson-shared-badge">ĐỒNG GIẢNG</span>}
          </div>
          <div className="tt-name">{lesson.courseName}</div>

          {/* Thanh mau do bao "co van de" - nhung mau khong noi duoc VAN DE GI.
              Popover phai tra loi cau do, neu khong thi mau chi la bao dong suong. */}
          {problems.length > 0 && (
            <div className="tt-problems">
              {problems.map((p) => {
                const meta = PROBLEM_META[p.type];
                // Ma lop hoc phan (vd "CSE3003-1") de hien THAY CHO "#<id noi
                // bo>" - p.sections da duoc buildProblemInbox() gan san
                // classCode cho tung buoi, chi can tra theo sectionId.
                const codeById = new Map(
                  (p.sections ?? []).map((s) => [s.sectionId ?? s.id, s.classCode]),
                );
                const other = (p.sectionIds?.filter((sid) => sid !== lesson.id) ?? [])
                  .map((sid) => codeById.get(sid) || `#${sid}`);
                const dropped = p.unplacedIds?.includes(lesson.id);
                return (
                  <div key={p.id} className={`tt-problem ${meta.cls}`}>
                    <div className="tt-problem-hd">
                      <span className="tt-problem-dot" aria-hidden="true" />
                      {meta.label}
                    </div>
                    <div className="tt-problem-body">
                      {/* Moi loai mot cach dien dat rieng: nhom "chua co gio" gom
                          theo DIEU PHOI VIEN, cac buoi trong nhom KHONG dung nhau
                          - viet "dung voi" o day la sai. */}
                      {p.type === "MISSING_HOURS" ? (
                        <>
                          Chưa có khung giờ nào được báo cho buổi này — giờ đang thấy trên lưới là do
                          thuật toán tự chọn trong cả tuần, chưa phải giờ điều phối viên xác nhận.
                        </>
                      ) : (
                        <>
                          {other.length > 0 && (
                            <>Đụng với <strong>{other.join(", ")}</strong>{p.when ? ` tại ${p.when}` : ""}. </>
                          )}
                          {dropped && <strong>Buổi này bị bỏ lại, không có trên lịch cuối.</strong>}
                        </>
                      )}
                    </div>
                    <div className="tt-problem-fix">{meta.fix}</div>
                    {onPickProblem && (
                      <button
                        type="button"
                        className="tt-problem-btn"
                        onClick={() => { onPickProblem(p); setLocked(false); }}
                      >
                        Mở trong hộp thư vấn đề →
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          <div className="tt-teacher-row">
            <span className="tt-label">Giảng viên</span>
            <strong>{lesson.teacherName}</strong>
          </div>
          <div className="tt-details">
            <div className="tt-detail-col">
              <span className="tt-label">Chương trình</span>
              <span className="tt-val">{lesson.programLabel}</span>
            </div>
            <div className="tt-detail-col">
              <span className="tt-label">Phòng</span>
              <span className="tt-val">{lesson.roomType}</span>
            </div>
          </div>
          <div className="tt-room-row">
            <span className="tt-label">Thời lượng</span>
            <span className="tt-val">{lesson.duration || 1} tiết{lesson.usedWindowLabel ? ` · ${lesson.usedWindowLabel}` : ""}</span>
          </div>

          {/* Buoi da bi keo-tha sua tay (ghim). Thay cho nut "Tu choi - luan
              chuyen" cu - gio keo-tha sang o khac lam viec do, popup nay chi con
              hien TRANG THAI ghim + cho bo ghim. */}
          {lesson.override && (
            <div className={`tt-pin-box ${lesson.override.problem ? "warn" : ""}`}>
              <div className="tt-pin-head">
                <span aria-hidden="true">📌</span> Đã ghim (sửa tay)
                {lesson.override.pinFailed && <span className="tt-pin-failed">— bị bỏ lại khi giải lại</span>}
              </div>
              {lesson.override.reason && <div className="tt-pin-reason">“{lesson.override.reason}”</div>}
              {lesson.override.problem?.teacherClashIds?.length > 0 && (
                <div className="tt-pin-conflict">
                  Đang trùng giờ với #{lesson.override.problem.teacherClashIds.join(", #")}
                </div>
              )}
              {lesson.override.problem?.roomFull && (
                <div className="tt-pin-conflict">
                  Hết phòng ({lesson.override.problem.sameRoomCount}/{lesson.override.problem.pool})
                </div>
              )}
              {onClearOverride && (
                <button
                  type="button"
                  className="tt-unpin-btn"
                  onClick={() => { onClearOverride(lesson.id); setLocked(false); }}
                >
                  Bỏ ghim
                </button>
              )}
            </div>
          )}

          {!locked && <div className="tt-hint">Bấm để giữ popup này mở</div>}
        </div>,
        document.body,
      )}
    </>
  );
});

export default LessonCard;

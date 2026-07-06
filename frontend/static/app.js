const eventPayloadElement = document.getElementById("event-payload");
const events = eventPayloadElement ? JSON.parse(eventPayloadElement.textContent || "[]") : [];
const eventMap = new Map(events.map((item) => [String(item.id), item]));
let selectedEventId = events[0] ? String(events[0].id) : null;
const activeJobPolls = new Set();

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function moneyLabel(value) {
  if (!value || value === "0") return "0원";
  const digits = String(value).replace(/\D/g, "");
  if (!digits) return escapeHtml(value);
  return `${Number(digits).toLocaleString("ko-KR")}원`;
}

function ddayClasses(state) {
  if (state === "urgent") return "bg-rose-600 text-white";
  if (state === "closed") return "bg-zinc-300 text-zinc-700";
  if (state === "unknown") return "bg-zinc-100 text-zinc-500";
  return "bg-blue-600 text-white";
}

function statusBadgeClasses(status, tone) {
  if (status === "완료") return tone === "gemini" ? "bg-violet-100 text-violet-800" : "bg-sky-100 text-sky-800";
  if (status === "실패") return "bg-rose-100 text-rose-800";
  if (status === "진행") return "bg-blue-100 text-blue-800";
  return "bg-zinc-100 text-zinc-500";
}

function resultText(result, fallback) {
  if (!result) return fallback;
  return result.detailed_analysis || result.risk_comment || result.item_details || fallback;
}

function modelResultMarkup(item, providerLabel, providerKey, alternativeKey) {
  let providerResults = item.analysis_results?.[providerKey] || {};
  if (!Object.keys(providerResults).length && alternativeKey) {
    providerResults = item.analysis_results?.[alternativeKey] || {};
  }
  if (!Object.keys(providerResults).length && providerKey === "chatgpt") {
    providerResults = item.analysis_results?.codex_cli || {};
  }
  const basic = providerResults.basic;
  const deep = providerResults.deep;
  const representative = deep || basic;
  if (!representative) {
    return `<div class="rounded-md border border-dashed border-white/15 bg-white/5 p-5 text-zinc-300">
      <p class="font-black text-white">${escapeHtml(providerLabel)} 분석 없음</p>
      <p class="mt-2 leading-7">이 모델의 결과가 아직 저장되지 않았습니다. 관리자 화면에서 분석 요청 또는 재분석을 진행할 수 있습니다.</p>
    </div>`;
  }
  return `<div class="space-y-4">
    <div class="grid gap-3 text-sm md:grid-cols-3">
      <div class="rounded-md border border-white/10 p-3"><p class="text-zinc-400">모델</p><p class="mt-1 font-black text-white">${escapeHtml(representative.model_name || representative.model_provider)}</p></div>
      <div class="rounded-md border border-white/10 p-3"><p class="text-zinc-400">분석 타입</p><p class="mt-1 font-black text-white">${deep ? "상세" : "기본"}</p></div>
      <div class="rounded-md border border-white/10 p-3"><p class="text-zinc-400">상태</p><p class="mt-1 font-black text-white">${escapeHtml(representative.status)}</p></div>
    </div>
    <div class="rounded-md border border-white/10 bg-white/5 p-5">
      <p class="text-sm font-black text-emerald-300">물건 요약</p>
      <p class="mt-2 whitespace-pre-wrap leading-7 text-zinc-100">${escapeHtml(representative.item_details || "확인 필요")}</p>
    </div>
    <div class="rounded-md border border-white/10 bg-white/5 p-5">
      <p class="text-sm font-black text-amber-300">리스크 판단</p>
      <p class="mt-2 whitespace-pre-wrap leading-7 text-zinc-100">${escapeHtml(representative.risk_comment || "확인 필요")}</p>
    </div>
    <div class="rounded-md border border-white/10 bg-white/5 p-5">
      <p class="text-sm font-black text-blue-300">상세/원문 기반 분석</p>
      <pre class="mt-2 max-h-[420px] overflow-auto whitespace-pre-wrap text-sm leading-7 text-zinc-100">${escapeHtml(resultText(deep, "상세 분석 결과는 아직 없습니다."))}</pre>
    </div>
  </div>`;
}

function comparisonMarkup(item) {
  const summary = item.comparison_summary || {};
  const stateClass = item.model_disagreement ? "border-amber-300 bg-amber-50 text-amber-950" : "border-emerald-300 bg-emerald-50 text-emerald-950";
  return `<div class="space-y-4 text-zinc-950">
    <div class="rounded-md border p-5 ${stateClass}">
      <p class="text-sm font-black">${item.dual_complete ? "두 모델 분석 완료" : "모델 분석 일부 미완료"}</p>
      <h3 class="mt-2 text-2xl font-black">${escapeHtml(summary.headline || "비교 준비 중")}</h3>
      <p class="mt-3 leading-7">${escapeHtml(summary.common || "")}</p>
      <p class="mt-2 leading-7">${escapeHtml(summary.difference || "")}</p>
    </div>
    <div class="grid gap-3 md:grid-cols-2">
      <div class="rounded-md border border-zinc-200 bg-white p-4">
        <p class="font-black text-violet-800">Gemini</p>
        <p class="mt-2 text-sm leading-6">${escapeHtml(item.gemini_status)}</p>
      </div>
      <div class="rounded-md border border-zinc-200 bg-white p-4">
        <p class="font-black text-sky-800">ChatGPT/Codex</p>
        <p class="mt-2 text-sm leading-6">${escapeHtml(item.chatgpt_status)}</p>
      </div>
    </div>
  </div>`;
}

function applyDdayBadge(element, state) {
  element.className = `dday-badge absolute right-3 top-3 rounded-full px-2.5 py-1 text-xs font-black ${ddayClasses(state)}`;
}

function detailMarkup(item, scope) {
  const deepReady = item.detailed_analysis && item.detailed_analysis.trim().length > 0;
  const rawText = item.raw_text || item.evidence_text || "저장된 원문 텍스트가 없습니다. 스캔 PDF 또는 HWP 파서 보강이 필요할 수 있습니다.";
  const marketReasons = (item.market_reasons || []).join(" / ") || "판단 사유 없음";
  const deepPanel = deepPanelMarkup(item, scope);
  const rawFileLink = item.raw_file_url
    ? `<a class="mt-4 inline-flex rounded-md bg-white px-4 py-2 text-sm font-black text-zinc-950" href="${escapeHtml(item.raw_file_url)}" target="_blank">원본 PDF/HWP 열기</a>`
    : "";

  return `
    <div class="grid min-h-full grid-cols-1 md:grid-cols-[1fr_1.12fr]">
      <section class="border-b border-zinc-200 p-5 md:border-b-0 md:border-r md:p-6">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="font-mono text-sm font-black text-emerald-700">${escapeHtml(item.case_number)}</p>
            <h2 class="mt-2 text-xl font-black leading-tight md:text-2xl">${escapeHtml(item.title)}</h2>
          </div>
          <span class="shrink-0 rounded-full px-3 py-1.5 text-sm font-black ${ddayClasses(item.d_day_state)}">${escapeHtml(item.d_day_str)}</span>
        </div>

        <div class="mt-5 rounded-md border border-amber-200 bg-amber-50 p-5">
          <p class="text-sm font-black text-amber-800">이 물건은 어떤 물건인가?</p>
          <p class="mt-2 whitespace-pre-wrap leading-7 text-amber-950">${escapeHtml(item.item_details)}</p>
        </div>

        <div class="mt-4 rounded-md border border-blue-200 bg-blue-50 p-5">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-black text-blue-800">상품성 매입/매각 기준</p>
            <span class="rounded-full bg-blue-700 px-3 py-1 text-sm font-black text-white">${escapeHtml(item.market_label)} ${escapeHtml(item.market_grade)}</span>
          </div>
          <p class="mt-2 leading-6 text-blue-950">${escapeHtml(marketReasons)}</p>
        </div>

        <dl class="mt-5 grid gap-4">
          <div class="grid grid-cols-2 gap-3">
            <div><dt class="text-xs font-bold text-zinc-500">대분류</dt><dd class="mt-1 text-lg font-black">${escapeHtml(item.main_category)}</dd></div>
            <div><dt class="text-xs font-bold text-zinc-500">세부 카테고리</dt><dd class="mt-1 text-lg font-black">${escapeHtml(item.sub_category)}</dd></div>
          </div>
          <div><dt class="text-xs font-bold text-zinc-500">소재지 또는 보관장소</dt><dd class="mt-1 leading-7">${escapeHtml(item.address)}</dd></div>
          <div class="grid grid-cols-2 gap-3">
            <div><dt class="text-xs font-bold text-zinc-500">최저매각가격</dt><dd class="mt-1 text-xl font-black">${moneyLabel(item.min_price)}</dd></div>
            <div><dt class="text-xs font-bold text-zinc-500">입찰일/매각기일</dt><dd class="mt-1 text-xl font-black">${escapeHtml(item.bidding_date)}</dd></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><dt class="text-xs font-bold text-zinc-500">작성일</dt><dd class="mt-1 font-bold">${escapeHtml(item.notice_date)}</dd></div>
            <div><dt class="text-xs font-bold text-zinc-500">공고만료일</dt><dd class="mt-1 font-bold">${escapeHtml(item.expire_date)}</dd></div>
          </div>
        </dl>
      </section>

      <section class="bg-zinc-950 p-5 text-white md:p-6">
        <div class="flex flex-wrap gap-2" data-tab-scope="${scope}">
          <button class="detail-tab rounded-md bg-white px-4 py-2 text-sm font-black text-zinc-950" data-target="summary" type="button">요약</button>
          <button class="detail-tab rounded-md border border-white/20 px-4 py-2 text-sm font-black text-zinc-300" data-target="schedule" type="button">가격/일정</button>
          <button class="detail-tab rounded-md border border-white/20 px-4 py-2 text-sm font-black text-zinc-300" data-target="deep" type="button">상세 분석</button>
          <button class="detail-tab rounded-md border border-white/20 px-4 py-2 text-sm font-black text-zinc-300" data-target="raw" type="button">원문 근거</button>
        </div>

        <div class="tab-panel mt-6" data-panel="summary">
          <p class="text-sm font-black text-emerald-300">AI 리스크 리포트</p>
          <h3 class="mt-2 text-2xl font-black md:text-3xl">권리분석 및 주의사항</h3>
          <div class="mt-5 rounded-md border border-white/10 bg-white/5 p-5">
            <p class="whitespace-pre-wrap text-base leading-8 text-zinc-100 md:text-lg">${escapeHtml(item.risk_comment)}</p>
          </div>
          <div class="mt-5 grid grid-cols-2 gap-3 text-sm">
            <div class="rounded-md border border-white/10 p-4"><p class="text-zinc-400">처리 상태</p><p class="mt-1 font-bold text-white">${escapeHtml(item.status)}</p></div>
            <div class="rounded-md border border-white/10 p-4"><p class="text-zinc-400">원문 저장</p><p class="mt-1 font-bold text-white">${item.raw_text_length.toLocaleString("ko-KR")}자</p></div>
            <div class="rounded-md border border-white/10 p-4"><p class="text-zinc-400">상세 페이지 증거</p><p class="mt-1 font-bold text-white">${item.evidence_text_length.toLocaleString("ko-KR")}자</p></div>
          </div>
        </div>

        <div class="tab-panel mt-6 hidden" data-panel="schedule">
          <h3 class="text-2xl font-black">가격/일정</h3>
          <div class="mt-5 grid gap-3 text-zinc-950 md:grid-cols-2">
            <div class="rounded-md bg-white p-4"><p class="text-sm font-bold text-zinc-500">최저매각가격</p><p class="mt-2 text-2xl font-black">${moneyLabel(item.min_price)}</p></div>
            <div class="rounded-md bg-white p-4"><p class="text-sm font-bold text-zinc-500">입찰일/매각기일</p><p class="mt-2 text-2xl font-black">${escapeHtml(item.bidding_date)}</p></div>
            <div class="rounded-md bg-white p-4"><p class="text-sm font-bold text-zinc-500">작성일</p><p class="mt-2 text-xl font-black">${escapeHtml(item.notice_date)}</p></div>
            <div class="rounded-md bg-white p-4"><p class="text-sm font-bold text-zinc-500">공고만료일</p><p class="mt-2 text-xl font-black">${escapeHtml(item.expire_date)}</p></div>
          </div>
        </div>

        <div class="tab-panel mt-6 hidden text-zinc-950" data-panel="deep">
          <h3 class="text-2xl font-black text-white">상세 심층 분석</h3>
          <div class="deep-content mt-4 text-zinc-950" data-event-id="${item.id}" data-scope="${scope}">
            ${deepPanel}
          </div>
        </div>

        <div class="tab-panel mt-6 hidden" data-panel="raw">
          <h3 class="text-2xl font-black">공고 원문</h3>
          ${rawFileLink}
          <pre class="mt-4 max-h-[520px] overflow-auto whitespace-pre-wrap rounded-md border border-white/10 bg-white/5 p-4 text-sm leading-7 text-zinc-100">${escapeHtml(rawText)}</pre>
        </div>

      </section>
    </div>
  `;
}

function jobLogMarkup(item) {
  const job = item.latest_job;
  const events = item.latest_events || [];
  const rows = events.slice(-12).map((event) => `
    <li class="rounded-md border border-white/10 bg-white/5 p-3">
      <p class="font-black text-white">${escapeHtml(event.event_type)}</p>
      <p class="mt-1 text-sm leading-6 text-zinc-300">${escapeHtml(event.message || "")}</p>
    </li>
  `).join("");
  return `<div class="space-y-4">
    <div class="grid gap-3 text-sm md:grid-cols-3">
      <div><p class="text-zinc-400">Job</p><p class="mt-1 font-black text-white">${job ? `#${job.id}` : "없음"}</p></div>
      <div><p class="text-zinc-400">상태</p><p class="mt-1 font-black text-white">${escapeHtml(job?.status || "요청 전")}</p></div>
      <div><p class="text-zinc-400">실행 모드</p><p class="mt-1 font-black text-white">${escapeHtml(job?.execution_mode || "-")}</p></div>
    </div>
    <ul class="space-y-2">${rows || "<li class='text-zinc-400'>최근 이벤트가 없습니다.</li>"}</ul>
  </div>`;
}

function bindScopedControls(container) {
  container.querySelectorAll(".detail-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const root = tab.closest("section");
      const target = tab.dataset.target;
      root.querySelectorAll(".detail-tab").forEach((button) => {
        const active = button.dataset.target === target;
        button.classList.toggle("bg-white", active);
        button.classList.toggle("text-zinc-950", active);
        button.classList.toggle("text-zinc-300", !active);
        button.classList.toggle("border", !active);
        button.classList.toggle("border-white/20", !active);
      });
      root.querySelectorAll(".tab-panel").forEach((panel) => {
        panel.classList.toggle("hidden", panel.dataset.panel !== target);
      });
    });
  });

  container.querySelectorAll(".deep-request-button").forEach((button) => {
    button.addEventListener("click", () => requestDeepAnalysis(button));
  });
  container.querySelectorAll(".deep-retry-button").forEach((button) => {
    button.addEventListener("click", () => retryDeepAnalysis(button));
  });
  container.querySelectorAll(".deep-cancel-button").forEach((button) => {
    button.addEventListener("click", () => cancelDeepAnalysis(button));
  });
  container.querySelectorAll(".deep-content").forEach((content) => {
    const item = eventMap.get(String(content.dataset.eventId));
    const job = item?.latest_job;
    if (job && (job.status === "PENDING" || job.status === "RUNNING")) {
      pollJob(job.id, item.id, content.dataset.scope);
    }
  });
}

function selectDesktop(eventId) {
  selectedEventId = String(eventId);
  document.querySelectorAll(".asset-row").forEach((row) => {
    const active = row.dataset.eventId === selectedEventId;
    row.classList.toggle("border-zinc-950", active);
    row.classList.toggle("ring-2", active);
    row.classList.toggle("ring-zinc-950", active);
  });

  const item = eventMap.get(selectedEventId);
  const emptyState = document.getElementById("empty-state");
  const detail = document.getElementById("desktop-detail");
  if (!item || !detail) return;

  emptyState?.classList.add("hidden");
  detail.classList.remove("hidden");
  detail.innerHTML = detailMarkup(item, "desktop");
  bindScopedControls(detail);
}

function toggleMobile(eventId) {
  const targetId = String(eventId);
  const panel = document.querySelector(`.mobile-detail[data-event-id="${targetId}"]`);
  const item = eventMap.get(targetId);
  if (!panel || !item) return;

  const isOpen = !panel.classList.contains("hidden");
  document.querySelectorAll(".mobile-detail").forEach((detail) => {
    detail.classList.add("hidden");
    detail.innerHTML = "";
  });

  if (isOpen) return;
  panel.classList.remove("hidden");
  panel.innerHTML = detailMarkup(item, `mobile-${targetId}`);
  bindScopedControls(panel);
}

function handleRowClick(row) {
  if (window.matchMedia("(min-width: 768px)").matches) {
    selectDesktop(row.dataset.eventId);
  } else {
    toggleMobile(row.dataset.eventId);
  }
}

function setFilter(filter) {
  document.querySelectorAll(".category-tab").forEach((tab) => {
    const active = tab.dataset.filter === filter;
    tab.classList.toggle("bg-zinc-950", active);
    tab.classList.toggle("text-white", active);
    tab.classList.toggle("bg-white", !active);
    tab.classList.toggle("border", !active);
    tab.classList.toggle("border-zinc-300", !active);
  });

  let firstVisible = null;
  document.querySelectorAll(".asset-card").forEach((card) => {
    const visible = filter === "전체" || card.dataset.category === filter;
    card.classList.toggle("hidden", !visible);
    if (visible && firstVisible === null) firstVisible = card.querySelector(".asset-row");
  });

  document.querySelectorAll(".mobile-detail").forEach((detail) => {
    detail.classList.add("hidden");
    detail.innerHTML = "";
  });

  if (firstVisible && window.matchMedia("(min-width: 768px)").matches) {
    selectDesktop(firstVisible.dataset.eventId);
  }
}

async function requestDeepAnalysis(button) {
  const eventId = button.dataset.eventId;
  const scope = button.dataset.scope;
  button.disabled = true;
  button.classList.add("opacity-60");

  try {
    const response = await fetch(`/api/analyze/deep/${eventId}/jobs`, { method: "POST" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "심층 분석 요청 실패");

    const item = eventMap.get(String(eventId));
    if (item) {
      item.latest_job = payload.job;
      item.detailed_analysis = payload.detailed_analysis || item.detailed_analysis || "";
    }
    renderDeepPanel(eventId, scope);
    if (payload.status === "cached") return;
    if (payload.job?.id) pollJob(payload.job.id, eventId, scope);
  } catch (error) {
    button.disabled = false;
    button.classList.remove("opacity-60");
    const status = document.querySelector(`.deep-status[data-event-id="${eventId}"][data-scope="${scope}"]`);
    if (status) status.textContent = error.message;
  }
}

function jobStatusLabel(status) {
  if (status === "PENDING") return "분석 대기 중";
  if (status === "RUNNING") return "분석 진행 중";
  if (status === "SUCCEEDED") return "분석 완료";
  if (status === "FAILED") return "분석 실패";
  if (status === "CANCELED") return "분석 취소됨";
  return "상세 분석 요청 가능";
}

function deepPanelMarkup(item, scope) {
  if (item.detailed_analysis && item.detailed_analysis.trim().length > 0) {
    return `<div class="deep-result whitespace-pre-wrap rounded-md border border-zinc-200 bg-white p-4 leading-7">${escapeHtml(item.detailed_analysis)}</div>`;
  }
  if (!item.has_analysis) {
    return `<div class="rounded-md border border-amber-200 bg-amber-50 p-5 leading-7 text-amber-900">기본 AI 분석이 없는 물건입니다. 파싱/OCR 상태를 먼저 확인해야 심층 분석을 요청할 수 있습니다.</div>`;
  }
  if (item.analysis_readiness && item.analysis_readiness.ready === false) {
    return `<div class="rounded-md border border-rose-200 bg-rose-50 p-5 leading-7 text-rose-900">
      <p class="font-black">분석 준비가 필요합니다.</p>
      <p class="mt-2">${escapeHtml(item.analysis_readiness.reason || "OCR/HWP/텍스트 상태를 확인해야 합니다.")}</p>
    </div>`;
  }

  const job = item.latest_job;
  if (job && (job.status === "PENDING" || job.status === "RUNNING")) {
    return `<div class="rounded-md border border-blue-200 bg-blue-50 p-5">
      <p class="text-lg font-black text-blue-950">${jobStatusLabel(job.status)}</p>
      <p class="mt-2 leading-7 text-blue-900">상세 분석을 준비하고 있습니다. 잠시 후 화면이 자동으로 갱신됩니다.</p>
      <div class="mt-4 h-2 overflow-hidden rounded-full bg-blue-100">
        <div class="h-full bg-blue-700" style="width:${Number(job.progress_percent || 0)}%"></div>
      </div>
      <div class="mt-4 flex flex-wrap items-center gap-2">
        <button class="deep-cancel-button rounded-md border border-blue-300 bg-white px-3 py-1.5 text-sm font-black text-blue-900" data-job-id="${job.id}" data-event-id="${item.id}" data-scope="${scope}" type="button">취소</button>
      </div>
      <p class="deep-status mt-3 text-sm font-semibold text-blue-700" data-event-id="${item.id}" data-scope="${scope}">상태를 확인하는 중입니다.</p>
    </div>`;
  }

  if (job && (job.status === "FAILED" || job.status === "CANCELED")) {
    return `<div class="rounded-md border border-rose-200 bg-rose-50 p-5">
      <p class="text-lg font-black text-rose-950">${jobStatusLabel(job.status)}</p>
      <p class="mt-2 whitespace-pre-wrap leading-7 text-rose-900">${escapeHtml(job.error_message || "작업이 완료되지 않았습니다.")}</p>
      <button class="deep-retry-button mt-4 rounded-md bg-rose-700 px-4 py-2 text-sm font-black text-white" data-job-id="${job.id}" data-event-id="${item.id}" data-scope="${scope}" type="button">재시도</button>
      <p class="deep-status mt-3 text-sm font-semibold text-rose-700" data-event-id="${item.id}" data-scope="${scope}"></p>
    </div>`;
  }

  return `<div class="rounded-md border border-dashed border-zinc-300 bg-zinc-50 p-5">
    <p class="leading-7 text-zinc-700">이 물건의 상세 심층 분석(권리관계, 가치 추정 등)을 로컬 분석 워커에게 요청하시겠습니까?</p>
    <button class="deep-request-button mt-4 rounded-md bg-zinc-950 px-4 py-2 text-sm font-black text-white" data-event-id="${item.id}" data-scope="${scope}" type="button">분석 요청</button>
    <p class="deep-status mt-3 text-sm font-semibold text-zinc-500" data-event-id="${item.id}" data-scope="${scope}"></p>
  </div>`;
}

function renderDeepPanel(eventId, scope) {
  const item = eventMap.get(String(eventId));
  const content = document.querySelector(`.deep-content[data-event-id="${eventId}"][data-scope="${scope}"]`);
  if (!item || !content) return;
  content.innerHTML = deepPanelMarkup(item, scope);
  bindScopedControls(content);
}

async function pollJob(jobId, eventId, scope) {
  const pollKey = `${jobId}:${scope}`;
  if (activeJobPolls.has(pollKey)) return;
  activeJobPolls.add(pollKey);
  await pollJobOnce(jobId, eventId, scope, pollKey);
}

async function pollJobOnce(jobId, eventId, scope, pollKey) {
  const item = eventMap.get(String(eventId));
  if (!item) {
    activeJobPolls.delete(pollKey);
    return;
  }
  try {
    const response = await fetch(`/api/analyze/jobs/${jobId}/events`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "작업 상태 조회 실패");
    item.latest_job = payload.job;
    item.latest_events = payload.events || [];
    if (payload.detailed_analysis) item.detailed_analysis = payload.detailed_analysis;
    renderDeepPanel(eventId, scope);
    if (payload.job?.status === "PENDING" || payload.job?.status === "RUNNING") {
      window.setTimeout(() => pollJobOnce(jobId, eventId, scope, pollKey), 3000);
    } else {
      activeJobPolls.delete(pollKey);
    }
  } catch (error) {
    activeJobPolls.delete(pollKey);
    const status = document.querySelector(`.deep-status[data-event-id="${eventId}"][data-scope="${scope}"]`);
    if (status) status.textContent = error.message;
  }
}

async function retryDeepAnalysis(button) {
  const jobId = button.dataset.jobId;
  const eventId = button.dataset.eventId;
  const scope = button.dataset.scope;
  const response = await fetch(`/api/analyze/jobs/${jobId}/retry`, { method: "POST" });
  const payload = await response.json();
  if (!response.ok) {
    const status = document.querySelector(`.deep-status[data-event-id="${eventId}"][data-scope="${scope}"]`);
    if (status) status.textContent = payload.detail || "재시도 실패";
    return;
  }
  const item = eventMap.get(String(eventId));
  if (item) item.latest_job = payload.job;
  renderDeepPanel(eventId, scope);
  pollJob(payload.job.id, eventId, scope);
}

async function cancelDeepAnalysis(button) {
  const jobId = button.dataset.jobId;
  const eventId = button.dataset.eventId;
  const scope = button.dataset.scope;
  const response = await fetch(`/api/analyze/jobs/${jobId}/cancel-request`, { method: "POST" });
  const payload = await response.json();
  const item = eventMap.get(String(eventId));
  if (response.ok && item) {
    item.latest_job = payload.job;
    renderDeepPanel(eventId, scope);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".dday-badge").forEach((badge) => {
    applyDdayBadge(badge, badge.dataset.state);
  });
  document.querySelectorAll(".asset-row").forEach((row) => {
    row.addEventListener("click", () => handleRowClick(row));
  });
  document.querySelectorAll(".category-tab").forEach((tab) => {
    tab.addEventListener("click", () => setFilter(tab.dataset.filter));
  });

  if (selectedEventId && window.matchMedia("(min-width: 768px)").matches) {
    selectDesktop(selectedEventId);
  }
});

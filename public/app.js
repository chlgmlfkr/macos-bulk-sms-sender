const form = document.querySelector("#sms-form");
const phoneListInput = document.querySelector("#phone-list");
const messageInput = document.querySelector("#message");
const statusBox = document.querySelector("#status");
const copyLinkButton = document.querySelector("#copy-link");
const nextLinkButton = document.querySelector("#next-link");
const recipientCount = document.querySelector("#recipient-count");
const queueProgress = document.querySelector("#queue-progress");

const MAX_RECIPIENTS = 20;
let deliveryQueue = [];
let currentRecipientIndex = -1;

function setStatus(message, type = "neutral") {
  statusBox.textContent = message;
  statusBox.dataset.state = type;
}

function normalizePhoneNumber(value) {
  const trimmed = value.trim();
  const hasLeadingPlus = trimmed.startsWith("+");
  const digitsOnly = trimmed.replace(/\D/g, "");

  if (!digitsOnly) {
    return "";
  }

  return hasLeadingPlus ? `+${digitsOnly}` : digitsOnly;
}

function parsePhoneNumbers(value) {
  const entries = value
    .split(/[\n,]/)
    .map((entry) => normalizePhoneNumber(entry))
    .filter(Boolean);

  const uniqueEntries = [...new Set(entries)];

  if (uniqueEntries.length === 0) {
    throw new Error("전화번호를 한 명 이상 입력하세요.");
  }

  if (uniqueEntries.length > MAX_RECIPIENTS) {
    throw new Error(`수신자는 최대 ${MAX_RECIPIENTS}명까지 입력할 수 있습니다.`);
  }

  for (const phone of uniqueEntries) {
    const digitCount = phone.replace(/\D/g, "").length;
    if (digitCount < 8) {
      throw new Error(`전화번호 형식이 너무 짧습니다: ${phone}`);
    }
  }

  return uniqueEntries;
}

function updateRecipientCount() {
  try {
    const recipients = parsePhoneNumbers(phoneListInput.value);
    recipientCount.textContent = `${recipients.length}명`;
  } catch {
    recipientCount.textContent = "0명";
  }
}

function updateQueueProgress() {
  if (currentRecipientIndex < 0 || deliveryQueue.length === 0) {
    queueProgress.textContent = "0 / 0";
    nextLinkButton.hidden = true;
    return;
  }

  queueProgress.textContent = `${Math.min(currentRecipientIndex + 1, deliveryQueue.length)} / ${deliveryQueue.length}`;
  nextLinkButton.hidden = currentRecipientIndex >= deliveryQueue.length - 1;
}

function buildSmsLink(phone, message) {
  return `sms:${phone}&body=${encodeURIComponent(message)}`;
}

function getFormData() {
  const phones = parsePhoneNumbers(phoneListInput.value);
  const message = messageInput.value.trim();

  if (!message) {
    throw new Error("문자 내용을 입력하세요.");
  }

  return { phones, message };
}

function openRecipientAt(index) {
  const message = messageInput.value.trim();

  if (!deliveryQueue.length || !message) {
    throw new Error("문자 내용을 입력하세요.");
  }

  currentRecipientIndex = index;
  updateQueueProgress();
  const phone = deliveryQueue[index];
  window.location.href = buildSmsLink(phone, message);
  setStatus(`${index + 1}번째 수신자(${phone}) 작성창을 열었습니다.`, "success");
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  try {
    const { phones } = getFormData();
    deliveryQueue = phones;
    openRecipientAt(0);
  } catch (error) {
    setStatus(error.message, "error");
  }
});

copyLinkButton.addEventListener("click", async () => {
  try {
    const { phones, message } = getFormData();
    const phone = currentRecipientIndex >= 0 ? deliveryQueue[currentRecipientIndex] : phones[0];
    const smsLink = buildSmsLink(phone, message);
    await navigator.clipboard.writeText(smsLink);
    setStatus("SMS 링크를 클립보드에 복사했습니다.", "success");
  } catch (error) {
    setStatus(error.message || "클립보드 복사에 실패했습니다.", "error");
  }
});

nextLinkButton.addEventListener("click", () => {
  try {
    if (!deliveryQueue.length) {
      const { phones } = getFormData();
      deliveryQueue = phones;
      openRecipientAt(0);
      return;
    }

    if (currentRecipientIndex >= deliveryQueue.length - 1) {
      setStatus("모든 수신자 작성창을 이미 열었습니다.", "neutral");
      updateQueueProgress();
      return;
    }

    openRecipientAt(currentRecipientIndex + 1);
  } catch (error) {
    setStatus(error.message, "error");
  }
});

phoneListInput.addEventListener("input", updateRecipientCount);
phoneListInput.addEventListener("input", () => {
  deliveryQueue = [];
  currentRecipientIndex = -1;
  updateQueueProgress();
});
messageInput.addEventListener("input", () => {
  if (currentRecipientIndex >= deliveryQueue.length) {
    currentRecipientIndex = -1;
    updateQueueProgress();
  }
});

updateRecipientCount();
updateQueueProgress();

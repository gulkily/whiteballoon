(() => {
  function initPanel(panel) {
    const form = panel.querySelector("[data-chat-ai-form]");
    const input = panel.querySelector("[data-chat-ai-input]");
    const transcript = panel.querySelector("[data-chat-ai-transcript]");
    const statusEl = panel.querySelector("[data-chat-ai-status]");
    const errorEl = panel.querySelector("[data-chat-ai-error]");
    const emptyEl = panel.querySelector("[data-chat-ai-empty]");
    const citationsEl = panel.querySelector("[data-chat-ai-citations]");
    const guardrailEl = panel.querySelector("[data-chat-ai-guardrail]");
    let conversationId = null;
    const scope = panel.getAttribute("data-chat-ai-scope") || "auto";
    const maxItems = parseInt(panel.getAttribute("data-chat-ai-max") || "5", 10);

    if (!form || !input || !transcript) {
      return;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const prompt = input.value.trim();
      if (!prompt) {
        return;
      }
      setLoading(true);
      clearError();
      try {
        const response = await fetch("/api/chat/ai", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            prompt,
            conversation_id: conversationId,
            context_scope: scope,
            max_context_items: maxItems,
          }),
        });
        if (!response.ok) {
          throw new Error(response.status === 401 ? "Sign in to use AI chat." : "AI request failed.");
        }
        const payload = await response.json();
        conversationId = payload.conversation_id;
        renderMessages(payload.messages || [], transcript, emptyEl);
        renderCitations(payload.citations || [], citationsEl);
        renderGuardrail(payload.guardrail_message, guardrailEl);
        input.value = "";
        input.focus();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unexpected error.";
        showError(message, errorEl);
      } finally {
        setLoading(false);
      }
    });

    function setLoading(isLoading) {
      const submitBtn = form.querySelector("[data-chat-ai-submit]");
      if (submitBtn) {
        submitBtn.setAttribute("aria-busy", isLoading ? "true" : "false");
        submitBtn.disabled = isLoading;
      }
      if (statusEl) {
        statusEl.hidden = !isLoading;
      }
      input.disabled = isLoading;
    }

    function clearError() {
      if (!errorEl) return;
      errorEl.hidden = true;
      errorEl.textContent = "";
    }
  }

  function renderMessages(messages, transcript, emptyEl) {
    transcript.innerHTML = "";
    if (emptyEl) {
      emptyEl.hidden = true;
    }
    if (!messages.length) {
      if (emptyEl) {
        emptyEl.hidden = false;
        transcript.appendChild(emptyEl);
      }
      return;
    }
    messages.forEach((message) => {
      const bubble = document.createElement("div");
      bubble.className = `chat-ai__message chat-ai__message--${message.role}`;
      bubble.textContent = message.content;
      transcript.appendChild(bubble);
    });
    transcript.scrollTop = transcript.scrollHeight;
  }

  function renderCitations(citations, container) {
    if (!container) return;
    container.innerHTML = "";
    if (!citations.length) {
      container.hidden = true;
      return;
    }
    container.hidden = false;
    const heading = document.createElement("h4");
    heading.textContent = "Sources";
    const list = document.createElement("ol");
    list.className = "chat-ai__citations-list";
    citations.forEach((citation) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = citation.url || "#";
      link.textContent = citation.label;
      link.target = "_blank";
      link.rel = "noreferrer";
      item.appendChild(link);
      if (citation.snippet) {
        const snippet = document.createElement("p");
        snippet.className = "small-text";
        snippet.textContent = citation.snippet;
        item.appendChild(snippet);
      }
      list.appendChild(item);
    });
    container.appendChild(heading);
    container.appendChild(list);
  }

  function renderGuardrail(message, container) {
    if (!container) return;
    if (!message) {
      container.hidden = true;
      container.textContent = "";
      return;
    }
    container.hidden = false;
    container.textContent = message;
  }

  function showError(message, container) {
    if (!container) return;
    container.hidden = false;
    container.textContent = message;
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-chat-ai-panel]").forEach((panel) => initPanel(panel));
  });
})();

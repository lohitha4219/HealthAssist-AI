import { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Bot,
  Check,
  Edit3,
  MessageSquarePlus,
  PanelLeftOpen,
  RefreshCw,
  Send,
  Sparkles,
  Trash2,
  User as UserIcon,
  X,
} from 'lucide-react';
import { chatService } from '../../services/chatAndReportService';
import { extractApiError } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import { GlassCard, LoadingSpinner, PageHeader } from '../../components/common/CommonUI';
import { formatTime } from '../../utils/formatters';
import './ChatPage.css';

const EXAMPLE_PROMPTS = [
  'What important questions should I ask my physician during an annual checkup?',
  'Explain what elevated serum creatinine or blood urea nitrogen indicates on a lab report.',
  'What cardiovascular warning signs require immediate emergency care (calling 108/112)?',
  'Which specialist should I consult for persistent joint swelling and morning stiffness?',
  'How do I find a verified cardiologist in Visakhapatnam, Tirupati, or Vijayawada?',
  'What dietary and lifestyle precautions help maintain healthy blood pressure levels?',
];

export function ChatPage() {
  const [aiHealth, setAiHealth] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loadingInit, setLoadingInit] = useState(true);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [sending, setSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const skipNextLoadRef = useRef(null);
  const { showToast } = useToast();

  const refreshAIHealth = async () => {
    try {
      const h = await chatService.getAIHealth();
      setAiHealth(h);
    } catch {
      // keep existing status
    }
  };

  useEffect(() => {
    let active = true;
    async function initChat() {
      setLoadingInit(true);
      try {
        const [healthData, convList] = await Promise.all([
          chatService.getAIHealth(),
          chatService.listConversations(),
        ]);
        if (!active) return;
        setAiHealth(healthData);
        setConversations(convList);
        if (convList.length > 0) {
          setActiveId(convList[0].id);
        }
      } catch (err) {
        if (active) setErrorMsg(extractApiError(err, 'Failed to load chat workspace'));
      } finally {
        if (active) setLoadingInit(false);
      }
    }
    initChat();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    if (skipNextLoadRef.current === activeId) {
      skipNextLoadRef.current = null;
      return;
    }
    let active = true;
    async function loadMessages() {
      setLoadingMsgs(true);
      setErrorMsg('');
      try {
        const detail = await chatService.getConversation(activeId);
        if (active) {
          setMessages(detail.messages || []);
        }
      } catch (err) {
        if (active) setErrorMsg(extractApiError(err, 'Failed to load conversation messages'));
      } finally {
        if (active) setLoadingMsgs(false);
      }
    }
    loadMessages();
    return () => {
      active = false;
    };
  }, [activeId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const handleNewChat = async () => {
    setErrorMsg('');
    try {
      const created = await chatService.createConversation();
      skipNextLoadRef.current = created.id;
      setConversations((prev) => [created, ...prev]);
      setActiveId(created.id);
      setMessages([]);
      setMobileHistoryOpen(false);
    } catch (err) {
      showToast(extractApiError(err, 'Could not start conversation'), 'error');
    }
  };

  const handleRenameSubmit = async (id) => {
    const trimmed = editingTitle.trim();
    if (!trimmed) {
      setEditingId(null);
      return;
    }
    try {
      const updated = await chatService.renameConversation(id, trimmed);
      setConversations((prev) => prev.map((c) => (c.id === id ? updated : c)));
      setEditingId(null);
      showToast('Conversation renamed', 'success');
    } catch (err) {
      showToast(extractApiError(err, 'Failed to rename conversation'), 'error');
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      await chatService.deleteConversation(id);
      const remaining = conversations.filter((c) => c.id !== id);
      setConversations(remaining);
      if (activeId === id) {
        setActiveId(remaining.length > 0 ? remaining[0].id : null);
        setMessages([]);
      }
      showToast('Conversation deleted', 'info');
    } catch (err) {
      showToast(extractApiError(err, 'Failed to delete conversation'), 'error');
    }
  };

  const submitPrompt = async (promptText) => {
    const text = (promptText ?? input).trim();
    if (!text || sending) return;

    setErrorMsg('');
    setSending(true);

    try {
      let targetConvId = activeId;
      if (!targetConvId) {
        const created = await chatService.createConversation();
        skipNextLoadRef.current = created.id;
        setConversations((prev) => [created, ...prev]);
        targetConvId = created.id;
        setActiveId(created.id);
      }

      if (promptText === undefined) {
        setInput('');
      }

      // Optimistically add user message and placeholder assistant message
      const tempUserMsg = {
        id: `temp-u-${Date.now()}`,
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      let streamedText = '';
      let streamSucceeded = false;

      try {
        await chatService.streamMessage(
          targetConvId,
          text,
          (chunk) => {
            streamedText += chunk;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.role === 'assistant' && last.id === 'streaming-assistant') {
                return [
                  ...prev.slice(0, -1),
                  { ...last, content: streamedText },
                ];
              }
              return [
                ...prev,
                {
                  id: 'streaming-assistant',
                  role: 'assistant',
                  content: streamedText,
                  created_at: new Date().toISOString(),
                },
              ];
            });
          },
          (donePayload) => {
            streamSucceeded = true;
            if (donePayload.title) {
              setConversations((prev) =>
                prev.map((c) =>
                  c.id === targetConvId ? { ...c, title: donePayload.title } : c
                )
              );
            }
          },
          (err) => {
            throw err;
          }
        );
      } catch (streamErr) {
        // Fallback to standard request if streaming not available and no text was received
        if (!streamSucceeded && !streamedText) {
          try {
            const res = await chatService.sendMessage(targetConvId, text);
            setMessages((prev) => [
              ...prev.filter((m) => m.id !== tempUserMsg.id && m.id !== 'streaming-assistant'),
              res.user_message,
              res.assistant_message,
            ]);
            setConversations((prev) => {
              const filtered = prev.filter((c) => c.id !== res.conversation.id);
              return [res.conversation, ...filtered];
            });
            streamSucceeded = true;
          } catch (sendErr) {
            throw sendErr;
          }
        } else {
          throw streamErr;
        }
      }

      // If streaming succeeded, refresh conversation detail in background
      if (streamSucceeded) {
        chatService
          .getConversation(targetConvId)
          .then((d) => {
            if (d && d.messages) {
              setMessages(d.messages);
            }
          })
          .catch(() => {});
        chatService.listConversations().then(setConversations).catch(() => {});
      }
    } catch (err) {
      if (promptText === undefined) {
        setInput(text);
      }
      setMessages((prev) =>
        prev.filter((m) => !String(m.id).startsWith('temp-') && m.id !== 'streaming-assistant')
      );
      const parsedError = extractApiError(
        err,
        'AI Assistant could not respond. Please configure GEMINI_API_KEY in backend/.env or check your cloud provider.'
      );
      setErrorMsg(parsedError);
      showToast(parsedError, 'error');
      refreshAIHealth();
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitPrompt();
    }
  };

  if (loadingInit) {
    return <LoadingSpinner label="Loading AI Chat Assistant..." />;
  }

  return (
    <div className="chat-page animate-fade-up">
      <PageHeader
        badge={
          <span
            className={`badge ${
              aiHealth?.available ? 'badge--success' : 'badge--warning'
            }`}
          >
            <Bot size={14} />
            {aiHealth?.available
              ? `AI Ready · ${aiHealth.provider.toUpperCase()} (${aiHealth.model})`
              : `AI Offline (${aiHealth?.status || 'unconfigured'})`}
          </span>
        }
        title="AI Chat Assistant"
        subtitle="Empathetic healthcare education, symptom explanation, lab report guidance, preventive wellness, and Andhra Pradesh hospital/doctor discovery."
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              type="button"
              className="btn btn--glass btn--sm chat-mobile-history-btn"
              onClick={() => setMobileHistoryOpen((o) => !o)}
            >
              <PanelLeftOpen size={16} /> History ({conversations.length})
            </button>
            <button
              type="button"
              className="btn btn--glass btn--sm"
              onClick={refreshAIHealth}
            >
              <RefreshCw size={15} /> Check AI Status
            </button>
          </div>
        }
      />

      {aiHealth && !aiHealth.available && (
        <div className="alert alert--warning" style={{ marginBottom: 16 }}>
          <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>AI Assistant Offline:</strong> {aiHealth.detail}
            <div style={{ fontSize: '0.84rem', marginTop: 4, opacity: 0.9 }}>
              {aiHealth.setup_hint}
            </div>
          </div>
        </div>
      )}

      <div className="chat-workspace">
        {/* Conversation History Sidebar */}
        <GlassCard
          padding="14px"
          className={`chat-sidebar ${mobileHistoryOpen ? 'is-open' : ''}`}
        >
          <button
            type="button"
            className="btn btn--primary"
            style={{ width: '100%', marginBottom: 12 }}
            onClick={handleNewChat}
          >
            <MessageSquarePlus size={17} /> New Conversation
          </button>

          <div className="chat-sidebar__list">
            {conversations.length === 0 ? (
              <div className="chat-sidebar__empty">
                No conversations yet. Click <strong>New Conversation</strong> or send a prompt.
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`chat-conv-item ${
                    conv.id === activeId ? 'is-active' : ''
                  }`}
                >
                  {editingId === conv.id ? (
                    <div className="chat-conv-edit">
                      <input
                        type="text"
                        className="field-input"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleRenameSubmit(conv.id);
                          if (e.key === 'Escape') setEditingId(null);
                        }}
                        autoFocus
                      />
                      <button
                        type="button"
                        className="chat-icon-btn"
                        aria-label="Save title"
                        onClick={() => handleRenameSubmit(conv.id)}
                      >
                        <Check size={15} />
                      </button>
                      <button
                        type="button"
                        className="chat-icon-btn"
                        aria-label="Cancel rename"
                        onClick={() => setEditingId(null)}
                      >
                        <X size={15} />
                      </button>
                    </div>
                  ) : (
                    <>
                      <button
                        type="button"
                        className="chat-conv-select"
                        onClick={() => {
                          setActiveId(conv.id);
                          setMobileHistoryOpen(false);
                        }}
                      >
                        <span className="chat-conv-title">{conv.title}</span>
                        <span className="chat-conv-preview">
                          {conv.last_message_preview || 'Empty conversation'}
                        </span>
                      </button>
                      <div className="chat-conv-actions">
                        <button
                          type="button"
                          className="chat-icon-btn"
                          aria-label={`Rename ${conv.title}`}
                          onClick={() => {
                            setEditingId(conv.id);
                            setEditingTitle(conv.title);
                          }}
                        >
                          <Edit3 size={14} />
                        </button>
                        <button
                          type="button"
                          className="chat-icon-btn chat-icon-btn--danger"
                          aria-label={`Delete ${conv.title}`}
                          onClick={() => handleDeleteConversation(conv.id)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </GlassCard>

        {/* Main Chat Area */}
        <GlassCard padding="0" className="chat-main">
          <div className="chat-messages">
            {loadingMsgs ? (
              <LoadingSpinner label="Loading messages..." />
            ) : messages.length === 0 ? (
              <div className="chat-welcome">
                <div className="chat-welcome__icon">
                  <Sparkles size={26} />
                </div>
                <h3>Ask Anything — General Knowledge, Code, or Health Info</h3>
                <p>
                  Conversations persist in PostgreSQL and keep follow-up context across sessions.
                </p>
                <div className="chat-prompts-grid">
                  {EXAMPLE_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      className="chat-prompt-chip glass-surface--subtle"
                      onClick={() => submitPrompt(prompt)}
                      disabled={sending}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`chat-bubble-row chat-bubble-row--${msg.role}`}
                >
                  <div className="chat-bubble-avatar">
                    {msg.role === 'user' ? <UserIcon size={16} /> : <Bot size={16} />}
                  </div>
                  <div className="chat-bubble">
                    <div className="chat-bubble__content">{msg.content}</div>
                    <div className="chat-bubble__meta">
                      <span>{formatTime(msg.created_at)}</span>
                      {msg.model_name && <span>· {msg.model_name}</span>}
                    </div>
                  </div>
                </div>
              ))
            )}

            {sending && (
              <div className="chat-bubble-row chat-bubble-row--assistant">
                <div className="chat-bubble-avatar">
                  <Bot size={16} />
                </div>
                <div className="chat-bubble chat-typing" aria-label="AI is generating response">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {errorMsg && (
            <div className="alert alert--error" style={{ margin: '0 18px 12px' }} role="alert">
              {errorMsg}
            </div>
          )}

          <div className="chat-input-bar">
            <textarea
              className="chat-textarea"
              rows={2}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sending}
              aria-label="Chat message input"
            />
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => submitPrompt()}
              disabled={sending || !input.trim()}
              aria-label="Send message"
            >
              <Send size={17} /> Send
            </button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

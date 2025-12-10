# BRD: AI-Powered Transcript Summarization

**ID:** BRD-2025-12-10-03  
**Created:** 2025-12-10  
**Status:** Draft  
**Priority:** Medium  
**Target Release:** v3.2

---

## Business Objective

### Why This is Needed

**Problem Statement:**
Users who transcribe videos (lectures, interviews, podcasts, meetings) currently receive only raw transcript text. Extracting key insights, action items, and summaries requires manual reading and analysis, which is time-consuming and error-prone, especially for long-form content.

**Background:**
- Transcription is just the first step in content analysis
- Users need actionable insights, not just raw text
- Manual summarization takes 10-30 minutes per hour of content
- AI chatbots (ChatGPT, Copilot, Gemini, Perplexity) excel at summarization
- Current workflow requires external tools (copy-paste to chatbot)
- Competitive advantage: integrated end-to-end solution

**Market Opportunity:**
- **Researchers:** Summarize academic lectures and interviews
- **Students:** Extract key points from online courses
- **Content Creators:** Generate video descriptions, social media posts
- **Business Users:** Summarize meetings, webinars, training sessions
- **Journalists:** Extract quotes and key facts from interviews
- **Podcasters:** Generate episode summaries and show notes

**Proposed Solution:**
Enable optional AI-powered summarization as a post-transcription step in the transcribe workflow. Users configure their preferred AI chatbot credentials once in the user profile, then receive automatic summaries appended to transcripts with source attribution.

**Workflow Integration:**
```
Transcribe workflow → Generate transcript.txt
        ↓
[OPTIONAL] AI Summarization (if enabled)
        ↓
Call AI chatbot with prompt "Summarize the key takeaways"
        ↓
Receive summary → Save as transcript_summary.txt
        ↓
Append "Source: [media_url]" to summary
```

---

## Stakeholder Requirements

### Primary Stakeholders

**1. Researchers & Academics**
- **Need:** Summarize research interviews, lectures, academic discussions
- **Expected Outcome:** Key findings, themes, quotes extracted automatically
- **Success Metric:** 80% time reduction in manual analysis

**2. Students & Learners**
- **Need:** Study notes from online courses and lectures
- **Expected Outcome:** Structured summaries with key concepts highlighted
- **Success Metric:** 70% faster study material preparation

**3. Content Creators (YouTube, Podcasts)**
- **Need:** Video descriptions, social media snippets, show notes
- **Expected Outcome:** Ready-to-publish summaries with source links
- **Success Metric:** 90% time reduction in description writing

**4. Business Users (Meetings, Training)**
- **Need:** Action items, decisions, key discussion points
- **Expected Outcome:** Meeting minutes with source attribution
- **Success Metric:** 85% time reduction in minutes preparation

**5. Journalists & Media**
- **Need:** Extract quotes, facts, storylines from interviews
- **Expected Outcome:** Structured interview highlights with timestamps
- **Success Metric:** 75% faster interview analysis

### Secondary Stakeholders

**6. Developers**
- **Impact:** New optional stage in transcribe workflow
- **Need:** Clean integration, user profile pattern reuse
- **Success Metric:** <400 LOC, AD-015 compliant

**7. System Administrators**
- **Impact:** External API dependencies (OpenAI, Microsoft, Google, Perplexity)
- **Need:** Secure credential storage, API rate limiting
- **Success Metric:** Zero credential leaks, graceful API failures

---

## Success Criteria

### Quantifiable Metrics

- [x] **Adoption:** 30%+ of transcribe workflow users enable summarization
- [x] **Success Rate:** 95%+ successful summaries (when API available)
- [x] **Performance:** <60 seconds additional time for typical transcript
- [x] **Quality:** 85%+ user satisfaction with summary quality
- [x] **Reliability:** <2% failure rate (excluding API outages)

### Qualitative Measures

- [x] **User Satisfaction:** Positive feedback on summary usefulness
- [x] **Workflow Simplification:** Eliminates external chatbot copy-paste
- [x] **Competitive Advantage:** Integrated solution vs. manual process
- [x] **Documentation Quality:** Clear setup instructions for all chatbots
- [x] **Error Handling:** Graceful degradation when API unavailable

---

## Scope

### In Scope

**Phase 1 (MVP - v3.2):**
- ✅ Optional summarization for transcribe workflow only
- ✅ Support for 4 AI chatbots:
  - ChatGPT (OpenAI API)
  - Microsoft Copilot (Azure OpenAI)
  - Google Gemini (Gemini API)
  - Perplexity AI (Perplexity API)
- ✅ User profile configuration (credentials per chatbot)
- ✅ Single prompt: "Summarize the key takeaways"
- ✅ Source attribution appended to summary
- ✅ Save summary as separate file (transcript_summary.txt)
- ✅ Enable/disable via job parameter (`--enable-summarization`)
- ✅ Graceful fallback (no summary if API fails)

**Phase 2 (Enhancement - v3.3):**
- ✅ Custom prompt templates per use case
- ✅ Summary formats (bullet points, paragraph, structured)
- ✅ Multi-language summaries (summarize in target language)
- ✅ Extend to translate workflow
- ✅ Token usage tracking and cost estimation

### Out of Scope

- ❌ Real-time summarization during transcription
- ❌ Interactive chat with AI about transcript
- ❌ Fine-tuned models (use provider's default models)
- ❌ Local LLM integration (Ollama, LLaMA)
- ❌ Subtitle workflow summarization (not applicable)
- ❌ Video content analysis (only transcript text)
- ❌ Multi-turn conversations with AI

### Future Considerations

**Post-v3.3 Enhancements:**
- Advanced prompt engineering (templates library)
- Sentiment analysis and topic extraction
- Timestamp-aware summaries (linked to video sections)
- Comparison summaries (multiple videos)
- Local LLM support (Ollama integration)
- Voice synthesis of summaries (text-to-speech)

---

## Dependencies

### Internal Dependencies

**Required CP-WhisperX Components:**
- ✅ `prepare-job.sh` - Extract AI chatbot credentials from user profile
- ✅ `shared/config_loader.py` - Configuration management
- ✅ `shared/user_profile.py` - User profile manager (AD-015)
- ✅ `shared/logger.py` - Logging infrastructure
- ✅ Transcribe workflow (Stage 01-07) - Must complete successfully

**Configuration Dependencies:**
- ✅ `config/.env.pipeline` - System-wide summarization settings
- ✅ `config/user.profile` - User-specific AI chatbot credentials (AD-015)
- ✅ Job directory structure - File placement

### External Dependencies

**AI Chatbot APIs:**
1. **OpenAI API (ChatGPT)**
   - Endpoint: https://api.openai.com/v1/chat/completions
   - Model: gpt-4-turbo (recommended) or gpt-3.5-turbo
   - Pricing: ~$0.01-0.03 per summary (typical)
   - Rate Limits: 10,000 requests/min (Tier 4)

2. **Azure OpenAI (Microsoft Copilot)**
   - Endpoint: https://{resource}.openai.azure.com/
   - Model: gpt-4 or gpt-35-turbo
   - Pricing: Similar to OpenAI
   - Rate Limits: Configurable per deployment

3. **Google Gemini API**
   - Endpoint: https://generativelanguage.googleapis.com/v1/
   - Model: gemini-pro
   - Pricing: Free tier available, then pay-as-you-go
   - Rate Limits: 60 requests/min (free), higher for paid

4. **Perplexity AI API**
   - Endpoint: https://api.perplexity.ai/chat/completions
   - Model: pplx-7b-online or pplx-70b-online
   - Pricing: $0.20-1.00 per 1M tokens
   - Rate Limits: Varies by plan

**Python Libraries:**
```
openai>=1.3.0           # OpenAI SDK
azure-openai>=1.0.0     # Azure OpenAI SDK
google-generativeai>=0.3.0  # Google Gemini SDK
perplexity-python>=1.0.0    # Perplexity SDK (if available)
```

### Prerequisites

**Before Implementation:**
- ✅ BRD-PRD-TRD approval
- ✅ Architecture review (AD-016: AI Summarization Architecture)
- ✅ API security audit (credential storage, rate limiting)
- ✅ Cost analysis (per-summary cost estimation)
- ✅ User profile extension (AD-015 compliance)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **API rate limiting** | Medium | Medium | Exponential backoff, queue mechanism, user notification |
| **API cost explosion** | High | Low | Per-user token limits, cost warnings, monthly caps |
| **Credential leakage** | High | Low | User profile storage (AD-015), never log credentials |
| **Poor summary quality** | Medium | Low | Model selection guidance, allow custom prompts (Phase 2) |
| **API outages** | Low | Medium | Graceful fallback (skip summarization), retry logic |
| **Long transcript timeout** | Medium | Low | Chunk large transcripts, configurable timeout |
| **Multiple API SDKs** | Medium | Low | Unified wrapper interface, handle version conflicts |
| **User expects free API** | Low | High | Clear documentation: user pays for API usage |

---

## Timeline & Resources

### Estimated Effort

**Total: 10-12 hours**

**Phase 1 (MVP - v3.2):**
- BRD-PRD-TRD Documentation: 3 hours ✅ (This document)
- Implementation: 5 hours
  - shared/ai_summarizer.py: 2 hours (unified API wrapper)
  - scripts/13_ai_summarization.py: 1.5 hours (new stage)
  - User profile extension: 0.5 hours (add [ai_chatbots] section)
  - prepare-job.sh integration: 0.5 hours (extract credentials)
  - Configuration: 0.5 hours
- Testing: 2 hours
  - Unit tests: 0.5 hours
  - Integration tests: 1 hour (all 4 APIs)
  - Manual testing: 0.5 hours
- Documentation: 2 hours
  - User guide: 1 hour (setup for each chatbot)
  - README updates: 0.5 hours
  - Troubleshooting: 0.5 hours

**Phase 2 (Enhancement - v3.3):**
- Custom prompts: 2 hours
- Summary formats: 1.5 hours
- Multi-language: 2 hours
- Token tracking: 1.5 hours

### Required Resources

**Development:**
- 1 developer (full-stack)
- API keys for all 4 chatbots (testing)
- Test transcripts (various lengths: 1min, 5min, 30min, 1hr)

**Testing:**
- API credits for testing (~$10-20 total)
- Various content types (lecture, interview, meeting, podcast)
- Network conditions (simulate API failures)

**Infrastructure:**
- No additional infrastructure needed
- Uses existing pipeline architecture
- External API calls only

---

## Business Value

### Revenue Impact

**Direct Revenue:**
- ✅ Premium feature differentiation (value-add)
- ✅ Increased user retention (complete solution)
- ✅ Competitive advantage (integrated workflow)

**Indirect Revenue:**
- ✅ Expanded addressable market (researchers, students, business users)
- ✅ Word-of-mouth marketing (unique feature)
- ✅ Upsell opportunity (API cost pass-through or markup)

### Cost Savings

**User Time:**
- Before: 10-30 minutes manual summarization per hour of content
- After: 0 minutes (automated)
- **Savings: 100% time reduction for summarization step**

**User Workflow:**
- Before: Transcribe → Copy to chatbot → Paste transcript → Wait → Copy summary → Save
- After: Transcribe with `--enable-summarization` → Done
- **Savings: 5 manual steps eliminated**

### Strategic Value

**Market Position:**
- ✅ End-to-end solution (transcribe → summarize → share)
- ✅ First-mover advantage (integrated AI summarization)
- ✅ Platform agnostic (user chooses chatbot)
- ✅ Extensible (custom prompts, formats in Phase 2)

**User Experience:**
- ✅ Simplified workflow (single command)
- ✅ Professional output (formatted summaries with sources)
- ✅ Reduced friction (no external tools needed)

---

## Compliance & Legal

### API Terms of Service

**OpenAI:**
- ✅ Comply with OpenAI usage policies
- ✅ Respect rate limits and quotas
- ✅ No redistribution of API responses
- ✅ User responsible for API costs

**Microsoft/Google/Perplexity:**
- ✅ Similar compliance requirements
- ✅ User owns output (summaries)
- ✅ No guarantees on availability

### Privacy Considerations

**Data Handling:**
- ✅ Transcripts sent to third-party APIs (user consent required)
- ✅ No storage of summaries by APIs (per provider policies)
- ✅ User credentials stored locally only (user profile)
- ✅ Clear documentation: "Transcript shared with [Provider]"

**User Consent:**
- ✅ Opt-in feature (disabled by default)
- ✅ Explicit `--enable-summarization` flag
- ✅ Warning: "Transcript will be shared with [Provider]"
- ✅ User controls which API to use

**Credential Security:**
- ✅ Stored in user profile (AD-015)
- ✅ Never logged or transmitted to us
- ✅ File permissions: 600 (user read/write only)
- ✅ User can delete profile anytime

---

## Approval & Sign-off

**Business Approval:**
- [ ] Product Owner: _____________________ Date: _______
- [ ] Business Stakeholder: ______________ Date: _______

**Technical Approval:**
- [ ] Lead Developer: ____________________ Date: _______
- [ ] Architect: _________________________ Date: _______

**Go/No-Go Decision:**
- [ ] **GO** - Proceed to PRD and implementation
- [ ] **NO-GO** - Defer or cancel with reason: ___________

---

## Related Documents

**Downstream Documents:**
- [PRD-2025-12-10-03-ai-summarization.md](../prd/PRD-2025-12-10-03-ai-summarization.md) (Next)
- [TRD-2025-12-10-03-ai-summarization.md](../trd/TRD-2025-12-10-03-ai-summarization.md) (Next)

**Reference Documents:**
- [DEVELOPER_STANDARDS.md](../../DEVELOPER_STANDARDS.md) - § 21 BRD-PRD-TRD Framework
- [BRD-PRD-TRD-IMPLEMENTATION-FRAMEWORK.md](../../../BRD-PRD-TRD-IMPLEMENTATION-FRAMEWORK.md)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) - AD-015 (User Profile), AD-016 (AI Summarization)

**Related BRDs:**
- [BRD-2025-12-10-02-online-media-integration.md](./BRD-2025-12-10-02-online-media-integration.md) - User profile pattern

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-10  
**Next Review:** Upon PRD completion

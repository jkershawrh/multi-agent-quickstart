# Arcade Video Talk Track: A Repeatable Blueprint for Enterprise AI Agents

**Target length:** 6–7 minutes  
**Audience:** Business leaders, architects, AI engineers, and platform teams  
**Recording format:** One continuous guided Arcade walkthrough  
**Primary message:** Red Hat's Agentic AI blueprint gives teams a repeatable way to turn a business outcome into a governed agent process. Intel Xeon provides the CPU foundation for the AI inference used within that process.

## Recording setup

Before recording:

1. Open the presentation at 1920×1080 or 1440×900.
2. Confirm the Red Hat and Intel logos render locally.
3. Confirm the application endpoint is healthy.
4. Run the live process once before recording to warm the services.
5. Verify that live results display `LIVE`. If the application displays `REHEARSAL` or `OFFLINE`, use the fallback wording below and do not describe the data as live.
6. Restart the presentation so no previous proof remains in session state.
7. Hide browser chrome where Arcade permits it and place the pointer away from important text.

## 0:00–0:35 — Opening

**Screen:** “Turn an AI idea into a repeatable business process”  
**Action:** Begin recording. Pause briefly before speaking.

**Narration:**

> Most organizations can create an impressive AI response. The harder question is whether they can turn that response into a business process they are prepared to own, operate, govern, and improve.
>
> This demonstration applies Red Hat's Agentic AI blueprint to that challenge. Red Hat provides the structure for deploying and governing the process on OpenShift, while Intel Xeon provides the CPU foundation for running the AI inference inside it.
>
> The goal is not simply to show multiple agents talking. It is to show a repeatable development method that starts with a business outcome and ends with an accountable decision.

**Action:** Advance to the business reframe.

## 0:35–1:10 — Reframe the agent

**Screen:** “An agent is a business process—not just an AI response”  
**Action:** Move the pointer from the left statement to the right statement.

**Narration:**

> On the left is the common pilot: a model, a prompt, and several tools can produce a useful answer, but ownership, evidence, and follow-through remain unclear.
>
> On the right is the operating model. We define the roles, approved information, controls, accountable owner, and measurable outcome before we treat the agent as a production process.
>
> The blueprint creates a shared language for the business team defining the outcome, the development team implementing the agent behavior, and the platform team operating it safely.

**Action:** Advance to the guided architecture.

## 1:10–3:15 — Five development decisions

**Screen:** “Five decisions turn an AI idea into an operating process”

### Decision 1 — Define

**Action:** Point to “1 · Define,” then reveal the technical boundary.

**Narration:**

> First, define the outcome. What request enters this process? What result should it produce? Who owns that result, and under which deployment policy?
>
> Here, that definition becomes a versioned workload deployed through Helm and GitOps on Red Hat OpenShift. Technology follows the operating decision instead of defining it.

**Action:** Select “Ask next question.”

### Decision 2 — Organize

**Action:** Reveal the answer.

**Narration:**

> Second, organize the responsibilities. We decide what people, agents, and applications each own while keeping one accountable workflow owner.
>
> The implementation uses an orchestrator and visible research, analysis, and execution roles. A2A is the cooperation mechanism underneath that process, not the business story itself.

**Action:** Select “Ask next question.”

### Decision 3 — Govern

**Action:** Reveal the answer.

**Narration:**

> Third, govern the process. Which information sources are approved? Which tools may each role use? Which action must pause for human approval?
>
> MCP exposes named capabilities, while allow-lists, policy, guardrails, and approval gates determine how those capabilities may be used. The model cannot grant itself access or permission.

**Action:** Select “Ask next question.”

### Decision 4 — Run

**Action:** Reveal the answer and point to the Intel Xeon CPU inference node.

**Narration:**

> Fourth, run each step on the level of AI capability it actually needs. Semantic routing can select an appropriate model tier without giving that model business authority.
>
> Intel Xeon provides the CPU inference foundation for these bounded AI work products. The model can generate and explain; it does not own the evidence, policy, or final action.

**Action:** Select “Ask next question.”

### Decision 5 — Improve

**Action:** Reveal the answer and trace from policy to human authority.

**Narration:**

> Fifth, preserve what the organization needs to review and improve the process: evidence, timing, model participation, policy decisions, and the human outcome.
>
> OpenShift isolation, Intel Xeon compute, proof records, and human approval create the implemented foundation. The wider blueprint provides a path toward stronger workload identity, sandboxing, gateway authorization, and end-to-end tracing as the process matures.

**Action:** Complete the architecture and advance to the live journey.

## 3:15–5:15 — Live business process

**Screen:** “Watch one business request become a governed decision”  
**Action:** Briefly point to the request: “Investigate INC-1042 and prepare—but do not execute—a remediation.”

**Narration:**

> Now we will run one concrete business request through the blueprint. The request is intentionally bounded: investigate the incident and prepare a remediation, but do not execute it.
>
> As the process runs, watch who participates, what approved evidence is used, where AI contributes, how long the work takes, and who owns the final decision.

### Live step 1 — Confirm capabilities

**Action:** Select “Start the live process.” Wait for the response before speaking.

**Narration when `LIVE`:**

> The live environment first discovers which specialist capabilities are available. It does not assume that every role is healthy or ready.

**Fallback narration when `REHEARSAL` or `OFFLINE`:**

> The endpoint is unavailable, so the presentation has clearly switched to labeled rehearsal data. The workflow remains demonstrable, but these values are not being presented as live evidence.

**Action:** Select the next live step.

### Live step 2 — Match effort to the request

**Narration:**

> A smaller request uses a shorter process. The result exposes the selected workflow, participating roles, AI service, and measured time to result. Routing changes the amount of work; it does not change who has authority.

**Action:** Select the next live step.

### Live step 3 — Build the recommendation

**Narration:**

> For the higher-stakes request, the process adds research, analysis, approved evidence, and execution context. Each role contributes a visible artifact, so the recommendation can be traced rather than accepted as one opaque answer.

**Action:** If useful, briefly open “Inspect technical topology,” trace the active path, then close it. Select the final live step.

### Live step 4 — Preserve accountable authority

**Narration:**

> The proposed action now reaches the policy boundary. Versioned policy determines that this action requires review, and the incident commander remains the accountable owner.
>
> This is the key separation: the LLM may help prepare and explain the recommendation, but model confidence never becomes permission to act.

**Action:** Advance to the adoption path.

## 5:15–5:55 — Adoption path

**Screen:** “Start with one process, then mature the shared foundation”  
**Action:** Move across Start, Standardize, and Scale.

**Narration:**

> This is an adoption path, not a big-bang platform project.
>
> Start by proving one accountable process and its outcome. Then standardize the reusable roles, tools, policies, deployment, and evidence requirements. Finally, add production controls such as stronger workload identity, sandboxing, gateway authorization, observability, and advanced inference routing as scale and risk require them.
>
> The blueprint lets the organization add those capabilities without redesigning the business process each time.

**Action:** Advance to the shared implementation model.

## 5:55–6:30 — One blueprint for three teams

**Screen:** “Business, development, and platform teams work from one blueprint”

**Narration:**

> The value of the blueprint is alignment.
>
> Business teams define the outcome, owner, evidence, decision, and acceptable risk. Development teams implement the responsibilities, collaboration, information access, and human handoffs. Platform teams operate that process on Red Hat OpenShift with Intel Xeon CPU inference and reusable production controls.
>
> A2A, MCP, and OpenAI-compatible inference remain open implementation choices beneath one shared operating model.

**Action:** Advance to the close.

## 6:30–7:00 — Close

**Screen:** “Build an agent process the organization can own”  
**Action:** Pause long enough for the proof status and evidence fields to be visible.

**Narration:**

> What we proved is not simply that several agents can cooperate. We showed a repeatable way to design, implement, govern, run, and improve an agent-enabled business process.
>
> Red Hat turns agent development into an operable and governed workload. Intel Xeon provides the CPU inference foundation that runs the bounded AI work inside it. Human owners retain authority over consequential action.
>
> The next step is the hands-on lab, where you apply this same blueprint to another process by changing its roles, evidence, AI work, policy, and approval boundary.

**Action:** End the recording before opening the lab.

## Short Arcade captions

Use these if Arcade requires concise step captions:

1. **Frame the outcome:** Move from an AI response to a business process the organization can own.
2. **Define:** Establish the request, expected result, accountable owner, and deployment policy.
3. **Organize:** Assign responsibilities across people, agents, and applications.
4. **Govern:** Approve evidence sources, tools, policy rules, and human decision points.
5. **Run:** Match each task to an appropriate model and Intel Xeon inference tier.
6. **Improve:** Preserve evidence, timing, policy, model participation, and human outcomes.
7. **Prove live:** Follow one request from capability discovery to accountable review.
8. **Adopt:** Prove one process, standardize the pattern, and add controls as it scales.
9. **Align teams:** Give business, development, and platform teams one shared blueprint.
10. **Continue:** Close the presentation, then apply the blueprint in the hands-on lab.

## Recording guardrails

- Say “live” only when the interface displays `LIVE`.
- If fallback data appears, explicitly call it rehearsal or offline data.
- Do not claim that sandbox API, SPIFFE identity, claims-based MCP Gateway, or llm-d replica routing is deployed unless the environment proves it.
- Describe Intel Xeon as the configured or intended CPU inference foundation unless the current environment exposes hardware evidence.
- Do not describe LLM output as evidence, policy, approval, or authority.
- Let each live result finish rendering before moving the pointer or continuing narration.
- End the presentation before opening the lab; the lab is the next journey.

class TopicSummaryWithSegments {
    topicSummary string
    segments SegmentRaw[]
}

class StudyInput {
    topics TopicSummaryWithSegments[]
    highlights string[]
}

class Flashcard {
    type FlashcardType
    front string
    back string
}

enum FlashcardType {
    BASIC_FACT
    EXPLANATION
    APPLICATION
    CONTEXT
}

function GenerateFlashcardsDetailed(input: StudyInput) -> Flashcard[] {
    client GeminiFlash2

    prompt #"
        Your task is to generate highly focused flashcards from highlighted content.
        
        **Goal:** For each highlight, identify 1-2 key concepts. Create 1-2 flashcards per concept maximum.
        **Important:** Highlights may contain extraction errors - use segments for accurate content and wording.

        Structured Content (Source of Truth for Answers):
        ---
        {% for topic_item in input.topics %}
        Topic Summary: {{ topic_item.topicSummary }}
        Segments for this topic:
            {% for segment in topic_item.segments %}
            - Segment Type: {{ segment.segment_type }}
            - Segment Text: {{ segment.segment_text }}
            {% endfor %}
        --- End of Topic: {{ topic_item.topicSummary }} ---
        {% endfor %}
        ---

        Highlighted Sections (may contain extraction errors):
        {% for highlight in input.highlights %}
        Highlight {{ loop.index }}:
        ---
        {{ highlight }}
        ---
        {% endfor %}

        **Process:**
        1. For each highlight, identify what concept it's pointing to (even if malformed)
        2. Find the corresponding well-formed content in the structured segments
        3. Identify 1-2 key testable concepts per highlight
        4. Create 1-2 flashcards maximum per concept using clean segment content
        5. Skip highlights that are too fragmented to interpret

        **Flashcard Types:**

        BASIC_FACT: For definitions, facts, data points
        - Front: What is [specific concept]?
        - Back: [precise definition from segments]

        EXPLANATION: For mechanisms, processes, reasoning
        - Front: Why/How does [phenomenon] work?
        - Back: [mechanism from segments]

        APPLICATION: For practical usage
        - Front: How is [concept] applied in [context]?
        - Back: [application steps from segments]

        CONTEXT: For relationships between concepts
        - Front: How does [concept A] relate to [concept B]?
        - Back: [relationship from segments]

        **Guidelines:**
        - Each card tests exactly one piece of knowledge
        - All answers MUST come from structured content, not highlights
        - Questions are specific and unambiguous
        - Answers don't repeat question phrasing
        - Skip overly obvious information
        - No cards requiring long lists

        {{ ctx.output_format }}

        JSON:
    "#
}

function GenerateFlashcardsSimple(input: StudyInput) -> Flashcard[] {
    client GeminiFlash2

    prompt #"
        Create focused flashcards from highlighted sections using structured content as the source of truth.
        
        **Constraints:** Maximum 2 cards per highlight. Only create cards for key concepts worth memorizing.
        **Important:** Highlights may have extraction errors - use segment text for accurate wording.

        Structured Content (Source of Truth for Answers):
        ---
        {% for topic_item in input.topics %}
        Topic Summary: {{ topic_item.topicSummary }}
        Segments for this topic:
            {% for segment in topic_item.segments %}
            - Segment Text: {{ segment.segment_text }}
            {% endfor %}
        --- End of Topic: {{ topic_item.topicSummary }} ---
        {% endfor %}
        ---

        Highlighted Sections (may contain extraction errors):
        {% for highlight in input.highlights %}
        Highlight {{ loop.index }}:
        ---
        {{ highlight }}
        ---
        {% endfor %}

        **Process:**
        1. For each highlight, identify what key concept it points to
        2. Find the accurate content in structured segments
        3. Create 1-2 simple question-answer pairs using segment content
        4. Skip highlights that are too unclear to interpret

        **Guidelines:**
        - Each card focuses on one specific concept from a highlight
        - All answers must come from structured content, not raw highlights
        - Avoid repeating question phrasing in answers
        - Keep cards straightforward and testable
        - Don't reference "the author" - treat content as factual
        - Skip obvious or trivial information

        {{ ctx.output_format }}

        JSON:
    "#
}
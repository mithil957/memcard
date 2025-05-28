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
        Your task is to generate highly focused, high-quality flashcards based on the provided "Highlighted Sections" and "Structured Content".
        
        **CRITICAL CONSTRAINTS - MUST FOLLOW:**
        1. **Maximum 1-2 flashcards per highlight** - No exceptions
        2. **One concept per highlight** - If a highlight contains multiple ideas, pick ONLY the single most important one
        3. **Skip poor highlights** - If a highlight is fragmented, incomplete, or unclear, skip it entirely
        4. **Zero tolerance for duplicates** - Never create cards that test essentially the same knowledge
        5. **Conceptual focus** - Prioritize understanding of key concepts over memorization of details

        **Accuracy Requirements:**
        - All answers MUST come from "Structured Content" using exact wording
        - Never use fragmented or incomplete highlight text for answers
        - If you can't find clear supporting content in segments, skip the highlight

        Structured Content (Authoritative Source for Answers):
        ---
        {% for topic_item in input.topics %}
        Topic: {{ topic_item.topicSummary }}
        Segments:
          {% for segment in topic_item.segments %}
          - Type: {{ segment.segment_type }}
            Text: {{ segment.segment_text }}
          {% endfor %}
        --- End of Topic ---
        {% endfor %}
        ---

        Highlighted Sections (Areas of Interest - may be fragmented from extraction errors):
        {% for highlight in input.highlights %}
        Highlight {{ loop.index }}:
        ---
        {{ highlight }}
        ---
        {% endfor %}

        **Card Creation Process:**
        For each highlight:
        1. **Assess quality**: Is this highlight clear and complete enough to identify a key concept? If not, SKIP.
        2. **Identify ONE concept**: What is the single most important, testable concept in this highlight?
        3. **Check for duplicates**: Have I already created a card testing this same knowledge? If yes, SKIP.
        4. **Find supporting content**: Can I find clear, complete information about this concept in the structured content? If not, SKIP.
        5. **Create card**: Make 1 card (or at most 2 if there are genuinely distinct aspects) using structured content for the answer.

        **Quality Filters - SKIP highlights that are:**
        - Sentence fragments or incomplete thoughts
        - Too technical/granular for meaningful testing
        - Redundant with concepts already covered
        - Unclear even with structured content context
        - Lists of multiple unrelated items

        **Flashcard Types:**

        BASIC_FACT: For key definitions, terms, or core concepts
        - Front: What is [specific concept]?
        - Back: [Clear definition from structured content]

        EXPLANATION: For mechanisms or "why/how" understanding  
        - Front: How/Why does [concept] work?
        - Back: [Mechanism from structured content]

        APPLICATION: For practical usage
        - Front: When/How is [concept] used?
        - Back: [Application from structured content]

        CONTEXT: For relationships between concepts
        - Front: How does [concept A] relate to [concept B]?
        - Back: [Relationship from structured content]

        **Final Quality Check:**
        - Each card tests exactly ONE piece of knowledge
        - Questions are specific and unambiguous
        - Answers are complete and sourced from structured content
        - No cards test trivial or overly detailed information
        - Maximum total cards should be roughly equal to number of good highlights

        {{ ctx.output_format }}

        JSON:
    "#
}

function GenerateFlashcardsSimple(input: StudyInput) -> Flashcard[] {
    client GeminiFlash2

    prompt #"
        Create focused flashcards from highlighted sections. Many highlights may be fragmented from extraction errors.
        
        **STRICT RULES:**
        - Maximum 1-2 cards per highlight
        - Skip fragmented, unclear, or incomplete highlights
        - Pick ONLY the most important concept per highlight
        - Zero duplicates allowed
        - All answers must use exact wording from structured content

        Structured Content (Authoritative Source for Answers):
        ---
        {% for topic_item in input.topics %}
        Topic: {{ topic_item.topicSummary }}
        Segments:
          {% for segment in topic_item.segments %}
          - Text: {{ segment.segment_text }}
          {% endfor %}
        --- End of Topic ---
        {% endfor %}
        ---

        Highlighted Sections (may be fragmented - use structured content for accuracy):
        {% for highlight in input.highlights %}
        Highlight {{ loop.index }}:
        ---
        {{ highlight }}
        ---
        {% endfor %}

        **Process for each highlight:**
        1. **Quality check**: Is this highlight clear enough to understand? If not, SKIP.
        2. **Find one concept**: What's the single most important idea here?
        3. **Duplicate check**: Already covered this concept? If yes, SKIP.
        4. **Create card**: Use structured content for accurate answer.

        **Guidelines:**
        - Front: Clear, specific question about the key concept
        - Back: Direct answer from structured content (no question repetition)
        - Focus on understanding, not memorizing details
        - Skip obvious or trivial information
        - Treat content as factual (no author references)

        {{ ctx.output_format }}

        JSON:
    "#
}
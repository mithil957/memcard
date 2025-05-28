class SegmentRaw {
  segment_type SegmentType @description("The type of the content in this segment.")
  segment_text string @description("The extracted text content of the segment, or a description if it's an image.")
}

function CheckMergeAcrossPageBreak(context_before_page_break: SegmentRaw[], context_after_page_break: SegmentRaw[]) -> bool {
  client GeminiFlash2

  prompt #"
    Analyze the boundary between the text segments provided before and after a potential page break.
    Focus EXCLUSIVELY on the relationship between the **VERY LAST segment BEFORE** the break and the **VERY FIRST segment AFTER** the break. The surrounding segments are provided for context only.

    Context Before Potential Break (ends with the last segment before):
    ---
    {{ context_before_page_break }}
    ---

    Context After Potential Break (starts with the first segment after):
    ---
    {{ context_after_page_break }}
    ---

    Your task is to determine if the **very first segment AFTER** the break MUST be joined with the **very last segment BEFORE** the break into ONE single segment. This should only happen if the page break interrupted the flow *mid-sentence*, *mid-paragraph-thought*, *mid-list-item*, or *mid-code-structure* within that boundary pair.

    - Output **true** ONLY if the first segment AFTER the break directly completes an obviously incomplete sentence, thought, list item, or code block started at the very end of the last segment BEFORE the break. Think: Was the last segment before the break cut off unnaturally mid-flow?

    - Output **false** in all other cases, **especially** if the first segment AFTER the break starts something logically distinct from the end of the last segment BEFORE the break, even if they are the same segment type (e.g., TEXT_BLOCK to TEXT_BLOCK, CODE_BLOCK to CODE_BLOCK). Examples of when to output **false**:
        - The first segment AFTER starts a new paragraph (look for paragraph structure, indentation, or a complete thought ending the last segment BEFORE).
        - The first segment AFTER starts a new, complete code statement, function definition, or logical block relative to the end of the segment BEFORE.
        - The first segment AFTER represents a natural transition or next step, rather than a direct continuation of an interrupted element from the segment BEFORE.
        - The last segment BEFORE ends with clear sentence-ending punctuation (. ! ?) and the first segment AFTER starts a new thought.

    Focus strictly on whether an **interruption** occurred *between the last segment before and the first segment after* that necessitates merging these two specific segments. Do **not** merge across standard paragraph breaks or logical code separations just because the topic is related or the segment types match.

    Respond ONLY with the boolean value: true or false.

    {{ ctx.output_format }}
  "#
}

test CheckMergeAcrossPageBreakFalse {
  functions [CheckMergeAcrossPageBreak]
  args {
    context_before_page_break [
      {
        segment_type CODE_BLOCK
        segment_text "$ rlwrap $QHOME/m32/q\nq)"
      },
      {
        segment_type HEADING
        segment_text "Configuration"
      },
      {
        segment_type TEXT_BLOCK
        segment_text "There are two important files in the installation. The first file is the q binary itself. It is located in the platform specific folder with a name like w32, s32, v32 or 132. The second file, q.k, is the file that defines many of the q operators. As previously mentioned, q is implemented as a mix of C, k, and q itself. The q.k file includes the implementation for many operators defined in k and q. Over time, a few of the operators previously implemented in q. k have been rewritten directly in C to increase performance. The complete list of operators defined in C can be found in the .Q.res variable."
      },
      {
        segment_type CODE_BLOCK
        segment_text "q).Q.res\n`in within like bin binr`ss`if do while ex\nec`select`insert`update`delete`av.."
      },
      {
        segment_type TEXT_BLOCK
        segment_text "The installation directory also contains another file named s.k which is used to implement an SQL interface for ODBC clients. It also provides an example of how to define other languages on top of k.\nOn startup, the q binary must load the q. k file to pick up the q definitions. For the q binary to find this file, you must first set the QHOME environment variable to the full path of the directory holding q.k. Once you have become more familiar with the q language, you can obtain a deeper understanding, and perhaps pick up a few coding pointers, by reading the q.k file."
      }
    ]

    context_after_page_break [
      {
        segment_type HEADING
        segment_text "Running q"
      },
      {
        segment_type TEXT_BLOCK
        segment_text "Now that the binary is installed, and the QHOME environment variable is configured, we can start the kdb+ process. Here is an example of running q on my laptop. [1]"
      },
      {
        segment_type CODE_BLOCK
        segment_text "$ ./m32/q\nKDB+ 3.2 2015.03.04 Copyright (C) 1993-2015 Kx Systems\nm32/4() core 2048MB nick nicks-macbook.local 192.168.1.103 NONEXPIRE"
      },
      {
        segment_type TEXT_BLOCK
        segment_text "There are few points to highlight here. On the first line of the banner, the 3.2 refers to the kdb+ version. This is followed by the q binary release date. On the second line, the m32 matches the architecture used to start the binary. 4() core indicates that kdb+ is capable of seeing 4 cores on my machine. If you purchase a production license, the number of licensed cores would appear within the parentheses. If you do not plan on using multiple cores per kdb+ instance, it is possible to reduce the number of cores visible to the q binary on *nix machines by changing the CPU affinity with the taskset utility. The number of available cores is followed by the system\'s available memory, login ID, machine name, IP address, an optional company name and license expiration date (\"NONEXPIRE\" in the case of the free 32-bit version)."
      },
      {
        segment_type HEADING
        segment_text "Customization"
      }
    ]
  }
}

test CheckMergeAcrossPageBreakTrue {
  functions [CheckMergeAcrossPageBreak]
  args {
    context_before_page_break [
      {
        segment_type HEADING
        segment_text ".stat.pctile"
      },
      {
        segment_type CODE_BLOCK
        segment_text "pctile:{[p;x]x iasc [x] -1+ceiling p*count x}"
      },
      {
        segment_type TEXT_BLOCK
        segment_text "can be equivalently defined in k. [2]"
      },
      {
        segment_type CODE_BLOCK
        segment_text "k)pctile:{[p;x]x(<x) -1+--p*#x}"
      },
      {
        segment_type TEXT_BLOCK
        segment_text "Another place the single backslash comes in handy is when q throws an exception. Q operators do their best to return the most appropriate value depending on the type and value of all parameters passed to them. For some combinations, however, there is no valid result. In these cases, an"
      }
    ]

    context_after_page_break [
      {
        segment_type TEXT_BLOCK
        segment_text "exception is thrown. When this happens, the calling function is suspended and the prompt is changed to display its directory and another layer of parentheses."
      },
      {
        segment_type CODE_BLOCK
        segment_text "q)1 mod `\nk){x-y*x div y}\n'type\ndiv\n1\nq.q))"
      },
      {
        segment_type TEXT_BLOCK
        segment_text "This indicates that q has entered the debugger. If we type another invalid statement, another layer of debugging is entered and another level of parentheses is displayed at the prompt. We will talk more about directories in Section 5.3 and the debugger in Chapter 13. Ctrl-c will not exit the debugger, and Ctrl-d and \"\\\" will quit the application. One way to return to the q) prompt is to type a single backslash \"\\\". This will exit one layer of debugging. Remember to type a single backslash for each level. Trying to exit multiple levels by typing a double backslash will exit the program, not the debugger." // Note: Escaped backslashes here
      },
      {
        segment_type TEXT_BLOCK
        segment_text "A single backslash can also be used in a q source file. Used as the only character on a line, a forward slash begins a multi-line comment. The multi-line comment continues until the end of file or a closing backslash is found. At any other location, a space followed by a forward slash comments the remainder of the line."
      },
      {
        segment_type CODE_BLOCK
        segment_text "/\nall text following a single forward slash\nis ignored until the end of a file"
      }
    ]
  }
}
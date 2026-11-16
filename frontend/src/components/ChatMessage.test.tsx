import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ChatMessageData } from "../api/types";
import { ChatMessage } from "./ChatMessage";

describe("ChatMessage", () => {
  it("renders the answer as markdown and expands real returned source details", () => {
    const message: ChatMessageData = {
      id: "answer-1",
      role: "assistant",
      content: "**Revenue** increased.",
      createdAt: "2026-11-16T12:00:00Z",
      sources: [{
        source_id: "source-1",
        document_id: "document-1",
        filename: "annual-report.pdf",
        page_number: 7,
        chunk_id: "chunk-1",
        excerpt: "Revenue grew during the year.",
      }],
    };
    render(<ChatMessage message={message} />);

    expect(screen.getByText("Revenue", { selector: "strong" })).toBeInTheDocument();
    fireEvent.click(screen.getByText("Sources (1)"));
    expect(screen.getByText("annual-report.pdf · Page 7")).toBeInTheDocument();
    expect(screen.getByText("Revenue grew during the year.")).toBeInTheDocument();
  });
});

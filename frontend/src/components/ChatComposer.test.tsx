import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ChatComposer } from "./ChatComposer";

describe("ChatComposer", () => {
  it("keeps send disabled for an empty question and sends on Enter", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatComposer mode="chat" busy={false} onModeChange={vi.fn()} onSend={onSend} />);
    const sendButton = screen.getByRole("button", { name: "Send question" });
    expect(sendButton).toBeDisabled();

    const input = screen.getByRole("textbox", { name: "Ask about your reports" });
    await user.type(input, "  Revenue trend?  ");
    expect(sendButton).toBeEnabled();
    await user.keyboard("{Enter}");
    expect(onSend).toHaveBeenCalledWith("Revenue trend?");
  });

  it("uses Shift+Enter for a line break and disables sends while busy", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatComposer mode="chat" busy onModeChange={vi.fn()} onSend={onSend} />);
    const input = screen.getByRole("textbox", { name: "Ask about your reports" });
    await user.type(input, "first line");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    expect(input).toHaveValue("first line\n");
    expect(screen.getByRole("button", { name: "Send question" })).toBeDisabled();
    expect(onSend).not.toHaveBeenCalled();
  });
});

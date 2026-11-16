import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthScreen } from "./AuthScreen";

describe("AuthScreen", () => {
  it("registers with the existing account API flow and returns to sign in", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue("registered");
    render(<AuthScreen busy={false} error="" notice="" onSubmit={onSubmit} />);

    await user.click(screen.getByRole("tab", { name: "Create account" }));
    await user.type(screen.getByLabelText("Email address"), "reader@example.com");
    await user.type(screen.getByLabelText("Password"), "A-unique-test-pass-42");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("register", "reader@example.com", "A-unique-test-pass-42"));
    expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    expect(screen.getByLabelText("Email address")).toHaveValue("reader@example.com");
  });

  it("shows API errors accessibly", () => {
    render(<AuthScreen busy={false} error="Could not reach the assistant." notice="" onSubmit={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Could not reach the assistant.");
  });
});

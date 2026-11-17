import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { UploadDialog } from "./UploadDialog";

describe("UploadDialog", () => {
  it("imports a public report link and fills Reliance metadata from its URL", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<UploadDialog busy={false} error="" onClose={vi.fn()} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("tab", { name: /from link/i }));
    const url = "https://www.ril.com/sites/default/files/reports/RIL-Integrated-Annual-Report-2025-26.pdf";
    await user.type(screen.getByLabelText("Public PDF link"), url);

    expect(screen.getByLabelText("Company")).toHaveValue("Reliance Industries Limited");
    expect(screen.getByLabelText("Reporting year")).toHaveValue(2026);
    await user.click(screen.getByRole("button", { name: "Import report" }));

    await waitFor(() =>
      expect(onSubmit).toHaveBeenCalledWith({
        source: "url",
        url,
        company: "Reliance Industries Limited",
        reportingYear: 2026,
        documentType: "annual_report",
      }),
    );
  });
});

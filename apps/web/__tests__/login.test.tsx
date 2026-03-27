import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { useRouter, useSearchParams } from "next/navigation";
import LoginPage from "../app/login/page";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";

const mockPush = jest.fn();
const mockGet = jest.fn();

declare global {
  var mockLocationHrefSetter: jest.Mock;
}

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
  (useSearchParams as jest.Mock).mockReturnValue({ get: mockGet });
  jest.spyOn(console, "error").mockImplementation((error) => {
    if (
      !(error?.message === "Not implemented: navigation (except hash changes)")
    ) {
      console.warn(error);
    }
  });
});

describe("LoginPage", () => {
  beforeEach(() => {
    localStorage.clear();
    (fetch as jest.MockedFunction<typeof fetch>).mockClear();
    mockPush.mockClear();
    mockGet.mockClear();
    global.mockLocationHrefSetter?.mockClear();
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {});
    jest.spyOn(Storage.prototype, "getItem").mockImplementation(() => null);
    jest.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("renders login page with app name and Google OAuth button", () => {
    render(<LoginPage />);

    expect(screen.getByText("Learning Space")).toBeInTheDocument();
    expect(
      screen.getByText("Sign in to your account to continue"),
    ).toBeInTheDocument();
    expect(screen.getByText("Google")).toBeInTheDocument();
  });


  it("initiates Google OAuth login when button is clicked", async () => {
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {});

    const mockResponse = {
      ok: true,
      json: jest.fn(() =>
        Promise.resolve({
          authorization_url:
            "https://accounts.google.com/authorize?state=test-state",
          provider: "google",
          state: "test-state",
        }),
      ),
    };
    (fetch as jest.Mock).mockResolvedValue(mockResponse);

    render(<LoginPage />);

    const googleButton = screen.getByText("Google");
    fireEvent.click(googleButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/auth/login/google",
      );
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "oauth_state_google",
      "test-state",
    );
  });

  it("shows error when Google OAuth initiation fails", async () => {
    (fetch as jest.Mock).mockResolvedValue({ ok: false, status: 400 });

    render(<LoginPage />);

    fireEvent.click(screen.getByText("Google"));

    await waitFor(() => {
      expect(
        screen.getByText("Failed to initiate Google login"),
      ).toBeInTheDocument();
    });
  });

  it("shows loading state during Google OAuth initiation", async () => {
    (fetch as jest.Mock).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: () =>
                  Promise.resolve({
                    authorization_url: "https://google.com",
                    state: "x",
                  }),
              }),
            100,
          ),
        ),
    );

    render(<LoginPage />);

    const googleButton = screen.getByText("Google");
    fireEvent.click(googleButton);

    // Button should be disabled while loading (spinner replaces it)
    expect(googleButton.closest("button")).toBeDisabled();
  });

});

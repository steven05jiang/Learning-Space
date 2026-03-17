// useMock — returns true when running in mock mode (NEXT_PUBLIC_USE_MOCK=true)
// Use this in data-fetching hooks to short-circuit API calls during UI development.
//
// Example:
//   const { data } = useResources();
//   // inside useResources:
//   if (useMock()) return { data: mockResources, isLoading: false, error: null };

export function useMock(): boolean {
  return process.env.NEXT_PUBLIC_USE_MOCK === "true";
}

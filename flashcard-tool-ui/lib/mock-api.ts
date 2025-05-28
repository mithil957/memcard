// Simulate delay for mock API calls
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Mock flashcard data by ID
const mockFlashcardData: Record<
  string,
  Array<{ question: string; answer: string; id: string }>
> = {
  auniqueid1231231: [
    {
      id: "card1",
      question: "What is Q?",
      answer:
        "Q is a vector programming language with first-class functions, descended from APL.",
    },
    {
      id: "card2",
      question: "What makes kdb+ efficient for time-series data?",
      answer:
        "Kdb+ uses a column-oriented design optimized for both in-memory and on-disk operations.",
    },
    {
      id: "card3",
      question: "How are updates performed in kdb+?",
      answer: "All updates in kdb+ are performed in a single thread.",
    },
    {
      id: "card4",
      question: "What industries commonly use kdb+?",
      answer: "Many financial institutions use kdb+ for tick data analysis.",
    },
    {
      id: "card5",
      question: "What is unique about kdb+?",
      answer:
        "Though in name it is a database, it is merely a programming language with database capabilities.",
    },
  ],
  // Add more mock data for other IDs as needed
};

// Mock API function to fetch flashcards by ID
export const mockFetchFlashcards = async (id: string) => {
  // Simulate network delay
  await delay(1500);

  // Simulate a 10% chance of error
  if (Math.random() < 0.05) {
    throw new Error("Failed to fetch flashcards");
  }

  // Return mock data if it exists for the ID
  if (mockFlashcardData[id]) {
    return mockFlashcardData[id];
  }

  // Return empty array if ID doesn't exist
  return [];
};

// Mock API function to submit flashcard ratings
export const mockSubmitRatings = async (
  id: string,
  ratings: Record<string, number | null>,
) => {
  // Simulate network delay
  await delay(1000);

  // Simulate a 10% chance of error
  if (Math.random() < 0.1) {
    throw new Error("Failed to submit ratings");
  }

  // Return success response
  return { success: true, message: "Ratings submitted successfully" };
};

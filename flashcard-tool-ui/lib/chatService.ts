interface MetadocumentResponse {
  message: string;
  metadocument: string;
}

export async function generateMetadocument(query: string): Promise<string> {
  const fastapiUrl = process.env.NEXT_PUBLIC_FASTAPI_URL;
  
  if (!fastapiUrl) {
    throw new Error("FASTAPI_URL is not defined. Please set this env variable");
  }

  const endpoint = `${fastapiUrl}/generate-metadocument`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {}
      const errorMessage =
        errorData?.detail ||
        `API Error: ${response.status} ${response.statusText}`;
      throw new Error(errorMessage);
    }

    const data: MetadocumentResponse = await response.json();
    return data.metadocument;
  } catch (error) {
    console.error("Error calling generateMetadocument API:", error);
    if (error instanceof Error) {
      throw new Error(
        `Failed to get response from chat service: ${error.message}`,
      );
    }
    throw new Error(
      "An unknown error occurred while fetching the metadocument.",
    );
  }
}

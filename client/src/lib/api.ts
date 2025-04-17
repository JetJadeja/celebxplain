// Celebrity type definition
export type Celebrity = {
  id: string;
  name: string;
  image: string;
};

// Job type definitions
export type JobRequest = {
  query: string;
  persona: string;
};

export interface JobUpdate {
  id: number;
  job_id: string;
  status: string;
  message: string;
  created_at: string;
}

export type JobResponse = {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed" | "error";
  created_at: string;
  completed_at?: string | null;
  error?: string;
  result_url?: string | null;
  persona_id?: string;
  query?: string;
  id?: string;
  updates?: JobUpdate[];
};

export type JobStatusResponse = {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed" | "error";
  result?: string;
  error?: string;
  created_at: string;
  updated_at: string;
};

// API base URL from environment variable
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

/**
 * Fetches all available personas/celebrities
 */
export async function fetchPersonas(): Promise<Celebrity[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/personas`);

    if (!response.ok) {
      throw new Error(`Failed to fetch personas: ${response.status}`);
    }

    const data = await response.json();

    // Transform the API response to match our Celebrity type
    return data.map((persona: any) => ({
      id: persona.id,
      name: persona.name,
      image: persona.icon_url,
    }));
  } catch (error) {
    console.error("Error fetching personas:", error);
    throw error;
  }
}

/**
 * Creates a new explanation job
 */
export async function createJob(
  query: string,
  personaId: string
): Promise<JobResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        persona: personaId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        errorData.error || `Failed to create job: ${response.status}`
      );
    }

    return response.json();
  } catch (error) {
    console.error("Error creating job:", error);
    throw error;
  }
}

/**
 * Fetches the status of a job
 */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch job status: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error fetching job status:", error);
    throw error;
  }
}

/**
 * Fetches the complete job with all updates
 */
export async function getJobWithUpdates(jobId: string): Promise<JobResponse> {
  try {
    // The API might not have a separate with-updates endpoint,
    // so let's just use the regular endpoint which should include updates
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch job with updates: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error fetching job with updates:", error);
    throw error;
  }
}

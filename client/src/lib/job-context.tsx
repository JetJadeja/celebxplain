"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { JobResponse, JobStatusResponse, createJob, getJobStatus } from "./api";

// Define the context state type
interface JobContextState {
  job: JobResponse | null;
  jobStatus: JobStatusResponse | null;
  loading: boolean;
  error: string | null;
  createNewJob: (query: string, personaId: string) => Promise<JobResponse>;
  clearJob: () => void;
  fetchJobById: (jobId: string) => Promise<void>;
}

// Create context with default values
const JobContext = createContext<JobContextState>({
  job: null,
  jobStatus: null,
  loading: false,
  error: null,
  createNewJob: async () => {
    throw new Error("JobContext not initialized");
  },
  clearJob: () => {},
  fetchJobById: async () => {},
});

// Hook for using the job context
export const useJob = () => useContext(JobContext);

interface JobProviderProps {
  children: ReactNode;
}

export const JobProvider = ({ children }: JobProviderProps) => {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(
    null
  );

  // Clear any existing polling when component unmounts
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Function to poll job status
  const pollJobStatus = async (jobId: string) => {
    try {
      console.log("Polling job status for:", jobId);
      const status = await getJobStatus(jobId);
      console.log("Received job status:", status);

      // Ensure job_id is set if it's missing in the response
      if (!status.job_id) {
        status.job_id = jobId;
      }

      setJobStatus(status);

      // If job is complete or failed, stop polling
      if (status.status === "completed" || status.status === "failed") {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
      }
    } catch (err) {
      console.error("Error polling job status:", err);
      setError(
        err instanceof Error ? err.message : "Failed to fetch job status"
      );
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
  };

  // Create a new job
  const createNewJob = async (
    query: string,
    personaId: string
  ): Promise<JobResponse> => {
    // Clear any previous job state
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }

    setLoading(true);
    setError(null);
    setJob(null);
    setJobStatus(null);

    try {
      console.log("Creating job with:", { query, persona: personaId });
      const newJob = await createJob(query, personaId);
      console.log("Created job:", newJob);

      // Ensure we have a job_id, fallback to a generated one if needed
      if (!newJob.job_id) {
        console.warn("Job ID missing in response, creating fallback ID");
        newJob.job_id = `fallback-${Date.now()}`;
      }

      setJob(newJob);

      // Return the job response so the caller can use it
      return newJob;
    } catch (err) {
      console.error("Error creating job:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to create job";
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Fetch job by ID
  const fetchJobById = async (jobId: string) => {
    // Clear any previous job state
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }

    setLoading(true);
    setError(null);

    try {
      // Set a minimal job object first
      const minimalJob: JobResponse = {
        job_id: jobId,
        status: "pending",
        created_at: new Date().toISOString(),
      };

      setJob(minimalJob);

      // Start polling for job status
      await pollJobStatus(jobId);

      const interval = setInterval(() => {
        pollJobStatus(jobId);
      }, 2000); // Poll every 2 seconds

      setPollingInterval(interval);
    } catch (err) {
      console.error("Error fetching job:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch job");
    } finally {
      setLoading(false);
    }
  };

  // Clear current job
  const clearJob = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
    setJob(null);
    setJobStatus(null);
    setError(null);
  };

  // Context value
  const value = {
    job,
    jobStatus,
    loading,
    error,
    createNewJob,
    clearJob,
    fetchJobById,
  };

  return <JobContext.Provider value={value}>{children}</JobContext.Provider>;
};

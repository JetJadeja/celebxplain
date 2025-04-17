"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useRef,
  useCallback,
} from "react";
import {
  JobResponse,
  JobStatusResponse,
  createJob,
  getJobStatus,
  getJobWithUpdates,
} from "./api";

// Define the context state type
interface JobContextState {
  job: JobResponse | null;
  jobStatus: JobStatusResponse | null;
  loading: boolean;
  error: string | null;
  createNewJob: (query: string, personaId: string) => Promise<JobResponse>;
  clearJob: () => void;
  fetchJobById: (jobId: string) => Promise<JobStatusResponse>;
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
  fetchJobById: async () => {
    throw new Error("JobContext not initialized");
  },
});

// Hook for using the job context
export const useJob = () => useContext(JobContext);

interface JobProviderProps {
  children: ReactNode;
}

export const JobProvider = ({ children }: JobProviderProps) => {
  // Use state for values that need to trigger re-renders
  const [job, setJob] = useState<JobResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use refs for tracking last fetch time to prevent too many fetches
  const lastFetchTime = useRef<{ [jobId: string]: number }>({});
  const isFetching = useRef<{ [jobId: string]: boolean }>({});

  // Create a new job
  const createNewJob = useCallback(
    async (query: string, personaId: string): Promise<JobResponse> => {
      setLoading(true);
      setError(null);
      setJob(null);
      setJobStatus(null);

      try {
        const newJob = await createJob(query, personaId);
        setJob(newJob);
        return newJob;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to create job";
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Fetch job by ID - completely simplified version
  const fetchJobById = useCallback(
    async (jobId: string): Promise<JobStatusResponse> => {
      // Prevent concurrent fetches for the same job ID
      if (isFetching.current[jobId]) {
        return Promise.resolve(
          jobStatus ||
            ({
              job_id: jobId,
              status: "pending",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            } as JobStatusResponse)
        );
      }

      // Check if we fetched recently (within 3 seconds)
      const now = Date.now();
      const lastFetch = lastFetchTime.current[jobId] || 0;

      if (now - lastFetch < 3000) {
        return Promise.resolve(
          jobStatus ||
            ({
              job_id: jobId,
              status: "pending",
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            } as JobStatusResponse)
        );
      }

      // Mark that we're fetching
      isFetching.current[jobId] = true;
      setLoading(true);

      try {
        // Update last fetch time
        lastFetchTime.current[jobId] = now;

        // Get job status
        const status = await getJobStatus(jobId);

        // Get full job if needed
        const fullJob = await getJobWithUpdates(jobId);

        // Update state only once with both pieces of data
        setJobStatus(status);
        setJob(fullJob);

        return status;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch job";
        setError(message);
        throw err;
      } finally {
        setLoading(false);
        isFetching.current[jobId] = false;
      }
    },
    [jobStatus]
  );

  // Clear current job
  const clearJob = useCallback(() => {
    setJob(null);
    setJobStatus(null);
    setError(null);
  }, []);

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

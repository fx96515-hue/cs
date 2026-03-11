"use client";

import React from "react";

interface LoadingStateProps {
  message?: string;
}

export default function LoadingState({ message = "Laden..." }: LoadingStateProps) {
  return (
    <div className="loadingState">
      <div className="loadingSpinner" />
      <div>{message}</div>
    </div>
  );
}

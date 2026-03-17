import { useState } from "react";

export const useScreenShare = () => {
  const [sharing, setSharing] = useState(false);

  const startShare = async () => {
    await navigator.mediaDevices.getDisplayMedia({ video: true });
    setSharing(true);
  };

  return { startShare, sharing };
};

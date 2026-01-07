import React from 'react';

// Get basePath from Next.js config (set at build time)
const basePath = process.env.__NEXT_ROUTER_BASEPATH || '';

export const BotAvatar = ({ height, width, size = 30, src = `${basePath}/nvidia.jpg` }) => {
  // Use size prop if height/width not provided
  const imgHeight = height || size;
  const imgWidth = width || size;
  
  const onError = (event: { target: { src: string } }) => {
    console.error('error loading bot avatar');
    event.target.src = `${basePath}/nvidia.jpg`;
  };

  return (
    <img
      src={src}
      alt="bot-avatar"
      width={imgWidth}
      height={imgHeight}
      className="rounded-full max-w-full h-auto"
      onError={onError}
    />
  );
};

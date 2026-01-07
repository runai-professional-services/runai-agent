import { DocumentProps, Head, Html, Main, NextScript } from 'next/document';

import i18nextConfig from '../next-i18next.config';
import { APPLICATION_UI_NAME } from '@/constants/constants';

type Props = DocumentProps & {
  // add custom document props
};

export default function Document(props: Props) {
  const currentLocale =
    props.__NEXT_DATA__.locale ?? i18nextConfig.i18n.defaultLocale;
  
  // Get basePath from Next.js build config
  const basePath = props.__NEXT_DATA__.basePath || '';
  
  // Construct the chat completion URL based on basePath
  // Use /generate/stream for streaming to avoid OAuth proxy 30s timeout
  const chatCompletionURL = basePath ? `${basePath}/generate/stream` : '/generate/stream';
  
  return (
    <Html lang={currentLocale}>
      <Head>
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta
          name="apple-mobile-web-app-title"
          content={APPLICATION_UI_NAME}
        ></meta>
        <script
          dangerouslySetInnerHTML={{
            __html: `window.__RUNTIME_ENV = {
              NEXT_PUBLIC_HTTP_CHAT_COMPLETION_URL: "${chatCompletionURL}",
              NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS: true
            };`,
          }}
        />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}

import { test as authTest } from '../fixtures/auth';
import { ResourcesPage } from '../fixtures/pages';

authTest.describe('@int_resources Resources smoke tests', () => {
  authTest.todo('user can view empty resource list');

  authTest.todo('user can submit a new resource with URL');

  authTest.todo('user can submit a resource with URL and custom title');

  authTest.todo('user can submit a resource with URL, title, and description');

  authTest.todo('user sees validation error for invalid URLs');

  authTest.todo('user sees duplicate warning when submitting existing URL');

  authTest.todo('user can view list of submitted resources');

  authTest.todo('user can search resources by title');

  authTest.todo('user can filter resources by processing status');

  authTest.todo('user can view resource details');

  authTest.todo('user can edit resource title and description');

  authTest.todo('user can delete a resource');

  authTest.todo('user sees processing status updates in real-time');

  authTest.todo('user can view processed resource with LLM-generated summary');

  authTest.todo('user can view processed resource with LLM-generated tags');

  authTest.todo('user can navigate to graph view from resource tags');

  authTest.todo('resource list updates automatically when new resources are added');

  authTest.todo('resource detail page updates when processing completes');

  authTest.todo('user can copy resource URL to clipboard');

  authTest.todo('user can share resource via social media links');
});
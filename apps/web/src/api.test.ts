import {describe,it,expect} from 'vitest';
import {displayMetric,safeSource} from './api';
describe('clinical data presentation',()=>{
  it('preserves missing values instead of implying zero or health',()=>{expect(displayMetric(null,'%')).toBe('—');expect(displayMetric(undefined)).toBe('—');expect(displayMetric(0,'%')).toBe('0%');});
  it('does not allow script or data source links',()=>{expect(safeSource('javascript:alert(1)')).toBeUndefined();expect(safeSource('data:text/html,bad')).toBeUndefined();expect(safeSource('https://www.nhs.uk/conditions/common-cold/')).toBe('https://www.nhs.uk/conditions/common-cold/');});
});
